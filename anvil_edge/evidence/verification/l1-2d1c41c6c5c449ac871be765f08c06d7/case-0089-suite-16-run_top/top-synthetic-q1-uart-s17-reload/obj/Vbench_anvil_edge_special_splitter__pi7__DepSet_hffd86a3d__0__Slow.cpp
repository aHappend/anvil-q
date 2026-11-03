// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vbench.h for the primary calling header

#include "Vbench__pch.h"
#include "Vbench__Syms.h"
#include "Vbench_anvil_edge_special_splitter__pi7.h"

VL_ATTR_COLD void Vbench_anvil_edge_special_splitter__pi7___stl_sequent__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__raw_specials__0(Vbench_anvil_edge_special_splitter__pi7* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+            Vbench_anvil_edge_special_splitter__pi7___stl_sequent__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__raw_specials__0\n"); );
    // Init
    IData/*31:0*/ __VdfgTmp_hb6edd8f3__0;
    __VdfgTmp_hb6edd8f3__0 = 0;
    // Body
    vlSelf->__PVT__splitter__DOT__special_selected 
        = ((0xbU == (IData)(vlSelf->__PVT__splitter__DOT__state)) 
           | (0xcU == (IData)(vlSelf->__PVT__splitter__DOT__state)));
    vlSelf->__PVT__splitter__DOT__special_flags = vlSelf->__PVT__splitter__DOT__special_record[1U];
    vlSelf->__Vcellinp__splitter__DOT__classification__in_scalar 
        = vlSelf->__PVT__splitter__DOT__scalars[(0xfU 
                                                 & vlSelf->__PVT__splitter__DOT__scalar_index)];
    vlSelf->__PVT__splitter__DOT__edge_end = (0x1ffffffffULL 
                                              & ((QData)((IData)(vlSelf->__PVT__splitter__DOT__edge_first)) 
                                                 + (QData)((IData)(vlSelf->__PVT__splitter__DOT__edge_count))));
    __VdfgTmp_hb6edd8f3__0 = vlSelf->__PVT__splitter__DOT__byte_ends
        [(0xfU & (vlSelf->__PVT__splitter__DOT__cursor 
                  - (IData)(1U)))];
    vlSelf->__PVT__splitter__DOT__classify_selected 
        = ((2U == (IData)(vlSelf->__PVT__splitter__DOT__state)) 
           | (3U == (IData)(vlSelf->__PVT__splitter__DOT__state)));
    vlSelf->__PVT__splitter__DOT__edge_selected = (
                                                   (0xfU 
                                                    == (IData)(vlSelf->__PVT__splitter__DOT__state)) 
                                                   | (0x10U 
                                                      == (IData)(vlSelf->__PVT__splitter__DOT__state)));
    vlSelf->in_ready = ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                        & (1U == (IData)(vlSelf->__PVT__splitter__DOT__state)));
    vlSelf->__PVT__busy = ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                           & ((0U != (IData)(vlSelf->__PVT__splitter__DOT__state)) 
                              & ((0x18U != (IData)(vlSelf->__PVT__splitter__DOT__state)) 
                                 & (0x19U != (IData)(vlSelf->__PVT__splitter__DOT__state)))));
    vlSelf->__PVT__splitter__DOT__class_ready = ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                                                 & (0U 
                                                    == (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__state)));
    vlSelf->__PVT__splitter__DOT__class_valid = ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                                                 & (6U 
                                                    == (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__state)));
    vlSelf->__PVT__splitter__DOT__encoder_ready = ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                                                   & (1U 
                                                      == (IData)(vlSelf->__PVT__splitter__DOT__encoder__DOT__state)));
    vlSelf->__PVT__splitter__DOT__encoder_valid = ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                                                   & (2U 
                                                      == (IData)(vlSelf->__PVT__splitter__DOT__encoder__DOT__state)));
    vlSelf->__PVT__splitter__DOT__record_ready = ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                                                  & (0U 
                                                     == (IData)(vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__state)));
    vlSelf->__PVT__splitter__DOT__edge_ready = ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                                                & (0U 
                                                   == (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__state)));
    vlSelf->__PVT__splitter__DOT__edge_valid = ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                                                & (0xaU 
                                                   == (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__state)));
    vlSelf->__Vcellinp__splitter__DOT__encoder__start 
        = ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
           & (4U == (IData)(vlSelf->__PVT__splitter__DOT__state)));
    vlSelf->__PVT__splitter__DOT__classification__DOT__reader_ready 
        = ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
           & (0U == (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state)));
    vlSelf->__PVT__splitter__DOT__classification__DOT__reader_valid 
        = ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
           & (0xaU == (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state)));
    vlSelf->out_valid = ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                         & (0x17U == (IData)(vlSelf->__PVT__splitter__DOT__state)));
    vlSelf->__PVT__splitter__DOT__record_valid = ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                                                  & (0xaU 
                                                     == (IData)(vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__state)));
    vlSelf->__PVT__splitter__DOT__class_rsp_ready = 
        ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
         & (8U == (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state)));
    vlSelf->__PVT__splitter__DOT__edge_rsp_ready = 
        ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
         & (8U == (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__state)));
    vlSelf->__PVT__splitter__DOT__record_rsp_ready 
        = ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
           & (8U == (IData)(vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__state)));
    vlSelf->__PVT__splitter__DOT__class_req = ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                                               & (7U 
                                                  == (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state)));
    vlSelf->__PVT__splitter__DOT__edge_req = ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                                              & (7U 
                                                 == (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__state)));
    vlSelf->__PVT__splitter__DOT__record_req = ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                                                & (7U 
                                                   == (IData)(vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__state)));
    vlSelf->__PVT__splitter__DOT__terminal_end = ((0U 
                                                   == vlSelf->__PVT__splitter__DOT__cursor)
                                                   ? 0U
                                                   : __VdfgTmp_hb6edd8f3__0);
    vlSelf->__VdfgTmp_hed1c005a__0 = (1U & ((~ (IData)(vlSelf->__PVT__splitter__DOT__classify_selected)) 
                                            & (~ (IData)(vlSelf->__PVT__splitter__DOT__edge_selected))));
    if (((~ (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__failed)) 
         & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__reader_valid))) {
        vlSelf->__PVT__splitter__DOT__classification__DOT__reader_data[0U] 
            = vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[0U];
        vlSelf->__PVT__splitter__DOT__classification__DOT__reader_data[1U] 
            = vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[1U];
        vlSelf->__PVT__splitter__DOT__classification__DOT__reader_data[2U] 
            = vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[2U];
        vlSelf->__PVT__splitter__DOT__classification__DOT__reader_data[3U] 
            = vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[3U];
    } else {
        vlSelf->__PVT__splitter__DOT__classification__DOT__reader_data[0U] = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__reader_data[1U] = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__reader_data[2U] = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__reader_data[3U] = 0U;
    }
    if (vlSelf->out_valid) {
        vlSelf->out_value = vlSelf->__PVT__splitter__DOT__output_value;
        vlSelf->out_special = vlSelf->__PVT__splitter__DOT__output_special;
        vlSelf->out_boundary = vlSelf->__PVT__splitter__DOT__output_boundary;
    } else {
        vlSelf->out_value = 0U;
        vlSelf->out_special = 0U;
        vlSelf->out_boundary = 0U;
    }
    if (vlSelf->__PVT__splitter__DOT__record_valid) {
        vlSelf->__PVT__splitter__DOT__record_error 
            = vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__failed;
        vlSelf->__PVT__splitter__DOT__record_code = vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__code;
    } else {
        vlSelf->__PVT__splitter__DOT__record_error = 0U;
        vlSelf->__PVT__splitter__DOT__record_code = 0U;
    }
    if (((~ (IData)(vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__failed)) 
         & (IData)(vlSelf->__PVT__splitter__DOT__record_valid))) {
        vlSelf->__PVT__splitter__DOT__record_data[0U] 
            = vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__result_data[0U];
        vlSelf->__PVT__splitter__DOT__record_data[1U] 
            = vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__result_data[1U];
        vlSelf->__PVT__splitter__DOT__record_data[2U] 
            = vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__result_data[2U];
        vlSelf->__PVT__splitter__DOT__record_data[3U] 
            = vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__result_data[3U];
    } else {
        vlSelf->__PVT__splitter__DOT__record_data[0U] = 0U;
        vlSelf->__PVT__splitter__DOT__record_data[1U] = 0U;
        vlSelf->__PVT__splitter__DOT__record_data[2U] = 0U;
        vlSelf->__PVT__splitter__DOT__record_data[3U] = 0U;
    }
    vlSelf->__PVT__splitter__DOT__eligible = (vlSelf->__PVT__splitter__DOT__special_record[1U] 
                                              & ((~ 
                                                  ((vlSelf->__PVT__splitter__DOT__special_record[1U] 
                                                    >> 3U) 
                                                   & (((0U 
                                                        != vlSelf->__PVT__splitter__DOT__scan_index) 
                                                       & (vlSelf->__PVT__splitter__DOT__properties
                                                          [
                                                          (0xfU 
                                                           & (vlSelf->__PVT__splitter__DOT__scan_index 
                                                              - (IData)(1U)))] 
                                                          >> 9U)) 
                                                      | ((vlSelf->__PVT__splitter__DOT__terminal_end 
                                                          < vlSelf->__PVT__splitter__DOT__scalar_count) 
                                                         & (vlSelf->__PVT__splitter__DOT__properties
                                                            [
                                                            ((0U 
                                                              == vlSelf->__PVT__splitter__DOT__cursor)
                                                              ? 0U
                                                              : 
                                                             (0xfU 
                                                              & __VdfgTmp_hb6edd8f3__0))] 
                                                            >> 9U))))) 
                                                 & ((1U 
                                                     & (vlSelf->__PVT__splitter__DOT__special_record[1U] 
                                                        >> 4U)) 
                                                    == (IData)(vlSelf->__PVT__splitter__DOT__phase))));
}

VL_ATTR_COLD void Vbench_anvil_edge_special_splitter__pi7___stl_sequent__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalized_specials__0(Vbench_anvil_edge_special_splitter__pi7* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+            Vbench_anvil_edge_special_splitter__pi7___stl_sequent__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalized_specials__0\n"); );
    // Init
    IData/*31:0*/ __VdfgTmp_hb6edd8f3__0;
    __VdfgTmp_hb6edd8f3__0 = 0;
    // Body
    vlSelf->__PVT__splitter__DOT__special_selected 
        = ((0xbU == (IData)(vlSelf->__PVT__splitter__DOT__state)) 
           | (0xcU == (IData)(vlSelf->__PVT__splitter__DOT__state)));
    vlSelf->__PVT__splitter__DOT__special_flags = vlSelf->__PVT__splitter__DOT__special_record[1U];
    vlSelf->__Vcellinp__splitter__DOT__classification__in_scalar 
        = vlSelf->__PVT__splitter__DOT__scalars[(0xfU 
                                                 & vlSelf->__PVT__splitter__DOT__scalar_index)];
    vlSelf->__PVT__splitter__DOT__edge_end = (0x1ffffffffULL 
                                              & ((QData)((IData)(vlSelf->__PVT__splitter__DOT__edge_first)) 
                                                 + (QData)((IData)(vlSelf->__PVT__splitter__DOT__edge_count))));
    __VdfgTmp_hb6edd8f3__0 = vlSelf->__PVT__splitter__DOT__byte_ends
        [(0xfU & (vlSelf->__PVT__splitter__DOT__cursor 
                  - (IData)(1U)))];
    vlSelf->__PVT__splitter__DOT__classify_selected 
        = ((2U == (IData)(vlSelf->__PVT__splitter__DOT__state)) 
           | (3U == (IData)(vlSelf->__PVT__splitter__DOT__state)));
    vlSelf->__PVT__splitter__DOT__edge_selected = (
                                                   (0xfU 
                                                    == (IData)(vlSelf->__PVT__splitter__DOT__state)) 
                                                   | (0x10U 
                                                      == (IData)(vlSelf->__PVT__splitter__DOT__state)));
    vlSelf->in_ready = ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                        & (1U == (IData)(vlSelf->__PVT__splitter__DOT__state)));
    vlSelf->__PVT__busy = ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                           & ((0U != (IData)(vlSelf->__PVT__splitter__DOT__state)) 
                              & ((0x18U != (IData)(vlSelf->__PVT__splitter__DOT__state)) 
                                 & (0x19U != (IData)(vlSelf->__PVT__splitter__DOT__state)))));
    vlSelf->__PVT__splitter__DOT__class_ready = ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                                                 & (0U 
                                                    == (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__state)));
    vlSelf->__PVT__splitter__DOT__class_valid = ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                                                 & (6U 
                                                    == (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__state)));
    vlSelf->__PVT__splitter__DOT__encoder_ready = ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                                                   & (1U 
                                                      == (IData)(vlSelf->__PVT__splitter__DOT__encoder__DOT__state)));
    vlSelf->__PVT__splitter__DOT__encoder_valid = ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                                                   & (2U 
                                                      == (IData)(vlSelf->__PVT__splitter__DOT__encoder__DOT__state)));
    vlSelf->__PVT__splitter__DOT__record_ready = ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                                                  & (0U 
                                                     == (IData)(vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__state)));
    vlSelf->__PVT__splitter__DOT__edge_ready = ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                                                & (0U 
                                                   == (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__state)));
    vlSelf->__PVT__splitter__DOT__edge_valid = ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                                                & (0xaU 
                                                   == (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__state)));
    vlSelf->__Vcellinp__splitter__DOT__encoder__start 
        = ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
           & (4U == (IData)(vlSelf->__PVT__splitter__DOT__state)));
    vlSelf->__PVT__splitter__DOT__classification__DOT__reader_ready 
        = ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
           & (0U == (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state)));
    vlSelf->__PVT__splitter__DOT__classification__DOT__reader_valid 
        = ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
           & (0xaU == (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state)));
    vlSelf->__PVT__splitter__DOT__record_valid = ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                                                  & (0xaU 
                                                     == (IData)(vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__state)));
    vlSelf->out_valid = ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                         & (0x17U == (IData)(vlSelf->__PVT__splitter__DOT__state)));
    vlSelf->__PVT__splitter__DOT__class_rsp_ready = 
        ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
         & (8U == (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state)));
    vlSelf->__PVT__splitter__DOT__edge_rsp_ready = 
        ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
         & (8U == (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__state)));
    vlSelf->__PVT__splitter__DOT__record_rsp_ready 
        = ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
           & (8U == (IData)(vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__state)));
    vlSelf->__PVT__splitter__DOT__class_req = ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                                               & (7U 
                                                  == (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state)));
    vlSelf->__PVT__splitter__DOT__edge_req = ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                                              & (7U 
                                                 == (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__state)));
    vlSelf->__PVT__splitter__DOT__record_req = ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                                                & (7U 
                                                   == (IData)(vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__state)));
    vlSelf->__PVT__splitter__DOT__terminal_end = ((0U 
                                                   == vlSelf->__PVT__splitter__DOT__cursor)
                                                   ? 0U
                                                   : __VdfgTmp_hb6edd8f3__0);
    vlSelf->__VdfgTmp_hed1c005a__0 = (1U & ((~ (IData)(vlSelf->__PVT__splitter__DOT__classify_selected)) 
                                            & (~ (IData)(vlSelf->__PVT__splitter__DOT__edge_selected))));
    if (((~ (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__failed)) 
         & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__reader_valid))) {
        vlSelf->__PVT__splitter__DOT__classification__DOT__reader_data[0U] 
            = vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[0U];
        vlSelf->__PVT__splitter__DOT__classification__DOT__reader_data[1U] 
            = vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[1U];
        vlSelf->__PVT__splitter__DOT__classification__DOT__reader_data[2U] 
            = vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[2U];
        vlSelf->__PVT__splitter__DOT__classification__DOT__reader_data[3U] 
            = vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[3U];
    } else {
        vlSelf->__PVT__splitter__DOT__classification__DOT__reader_data[0U] = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__reader_data[1U] = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__reader_data[2U] = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__reader_data[3U] = 0U;
    }
    if (vlSelf->__PVT__splitter__DOT__record_valid) {
        vlSelf->__PVT__splitter__DOT__record_error 
            = vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__failed;
        vlSelf->__PVT__splitter__DOT__record_code = vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__code;
    } else {
        vlSelf->__PVT__splitter__DOT__record_error = 0U;
        vlSelf->__PVT__splitter__DOT__record_code = 0U;
    }
    if (((~ (IData)(vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__failed)) 
         & (IData)(vlSelf->__PVT__splitter__DOT__record_valid))) {
        vlSelf->__PVT__splitter__DOT__record_data[0U] 
            = vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__result_data[0U];
        vlSelf->__PVT__splitter__DOT__record_data[1U] 
            = vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__result_data[1U];
        vlSelf->__PVT__splitter__DOT__record_data[2U] 
            = vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__result_data[2U];
        vlSelf->__PVT__splitter__DOT__record_data[3U] 
            = vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__result_data[3U];
    } else {
        vlSelf->__PVT__splitter__DOT__record_data[0U] = 0U;
        vlSelf->__PVT__splitter__DOT__record_data[1U] = 0U;
        vlSelf->__PVT__splitter__DOT__record_data[2U] = 0U;
        vlSelf->__PVT__splitter__DOT__record_data[3U] = 0U;
    }
    if (vlSelf->out_valid) {
        vlSelf->out_value = vlSelf->__PVT__splitter__DOT__output_value;
        vlSelf->out_special = vlSelf->__PVT__splitter__DOT__output_special;
        vlSelf->out_boundary = vlSelf->__PVT__splitter__DOT__output_boundary;
    } else {
        vlSelf->out_value = 0U;
        vlSelf->out_special = 0U;
        vlSelf->out_boundary = 0U;
    }
    vlSelf->__PVT__splitter__DOT__eligible = (vlSelf->__PVT__splitter__DOT__special_record[1U] 
                                              & ((~ 
                                                  ((vlSelf->__PVT__splitter__DOT__special_record[1U] 
                                                    >> 3U) 
                                                   & (((0U 
                                                        != vlSelf->__PVT__splitter__DOT__scan_index) 
                                                       & (vlSelf->__PVT__splitter__DOT__properties
                                                          [
                                                          (0xfU 
                                                           & (vlSelf->__PVT__splitter__DOT__scan_index 
                                                              - (IData)(1U)))] 
                                                          >> 9U)) 
                                                      | ((vlSelf->__PVT__splitter__DOT__terminal_end 
                                                          < vlSelf->__PVT__splitter__DOT__scalar_count) 
                                                         & (vlSelf->__PVT__splitter__DOT__properties
                                                            [
                                                            ((0U 
                                                              == vlSelf->__PVT__splitter__DOT__cursor)
                                                              ? 0U
                                                              : 
                                                             (0xfU 
                                                              & __VdfgTmp_hb6edd8f3__0))] 
                                                            >> 9U))))) 
                                                 & ((1U 
                                                     & (vlSelf->__PVT__splitter__DOT__special_record[1U] 
                                                        >> 4U)) 
                                                    == (IData)(vlSelf->__PVT__splitter__DOT__phase))));
}
