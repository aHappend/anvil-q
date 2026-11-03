// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vbench.h for the primary calling header

#include "Vbench__pch.h"
#include "Vbench__Syms.h"
#include "Vbench_anvil_edge_normalizer__M10.h"

VL_ATTR_COLD void Vbench_anvil_edge_normalizer__M10___stl_sequent__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalization__0(Vbench_anvil_edge_normalizer__M10* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+              Vbench_anvil_edge_normalizer__M10___stl_sequent__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalization__0\n"); );
    // Init
    CData/*0:0*/ __VdfgTmp_hd39cf095__0;
    __VdfgTmp_hd39cf095__0 = 0;
    // Body
    vlSelf->__PVT__normalizer__DOT__record_scalar_valid 
        = ((~ ((0xd800U <= vlSelf->__PVT__normalizer__DOT__record_value[0U]) 
               & (0xdfffU >= vlSelf->__PVT__normalizer__DOT__record_value[0U]))) 
           & (0x10ffffU >= vlSelf->__PVT__normalizer__DOT__record_value[0U]));
    vlSelf->__PVT__normalizer__DOT__pool_end = (0x1ffffffffULL 
                                                & ((QData)((IData)(
                                                                   vlSelf->__PVT__normalizer__DOT__record_value[1U])) 
                                                   + (QData)((IData)(
                                                                     vlSelf->__PVT__normalizer__DOT__record_value[2U]))));
    vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__shifted_remainder 
        = (0x1ffffffffULL & (VL_SHIFTL_QQI(33,33,32, vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__remainder_work, 1U) 
                             | (QData)((IData)((vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__dividend_shift 
                                                >> 0x1fU)))));
    __VdfgTmp_hd39cf095__0 = (vlSelf->__PVT__normalizer__DOT__record_value[0U] 
                              == vlSelf->__PVT__normalizer__DOT__starter_scalar);
    vlSelf->__PVT__normalizer__DOT__classify_selected 
        = ((0xaU == (IData)(vlSelf->__PVT__normalizer__DOT__state)) 
           | (0xbU == (IData)(vlSelf->__PVT__normalizer__DOT__state)));
    vlSelf->__PVT__normalizer__DOT__pool_selected = 
        ((7U == (IData)(vlSelf->__PVT__normalizer__DOT__state)) 
         | (8U == (IData)(vlSelf->__PVT__normalizer__DOT__state)));
    if (vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) {
        vlSelf->in_ready = (1U == (IData)(vlSelf->__PVT__normalizer__DOT__state));
        vlSelf->__PVT__normalizer__DOT__record_ready 
            = (0U == (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__state));
        vlSelf->__PVT__normalizer__DOT__record_valid 
            = (0xaU == (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__state));
        vlSelf->__PVT__normalizer__DOT__pool_ready 
            = (0U == (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__state));
        vlSelf->__PVT__normalizer__DOT__pool_valid 
            = (0xaU == (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__state));
        vlSelf->__PVT__normalizer__DOT__divider_ready 
            = (0U == (IData)(vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__state));
        vlSelf->__PVT__normalizer__DOT__quotient = vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__quotient_result;
        vlSelf->__PVT__normalizer__DOT__remainder_value 
            = vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__remainder_result;
        vlSelf->__PVT__normalizer__DOT__class_ready 
            = (0U == (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__state));
        vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_ready 
            = (0U == (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state));
        vlSelf->__PVT__normalizer__DOT__divider_valid 
            = (3U == (IData)(vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__state));
        vlSelf->out_valid = (0x24U == (IData)(vlSelf->__PVT__normalizer__DOT__state));
        vlSelf->__PVT__normalizer__DOT__class_valid 
            = (6U == (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__state));
        vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_valid 
            = (0xaU == (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state));
        vlSelf->__PVT__normalizer__DOT__class_tbl_ready 
            = (8U == (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state));
        vlSelf->__PVT__normalizer__DOT__pool_tbl_ready 
            = (8U == (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__state));
        vlSelf->__PVT__normalizer__DOT__record_tbl_ready 
            = (8U == (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__state));
        vlSelf->__PVT__normalizer__DOT__class_tbl_valid 
            = (7U == (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state));
        vlSelf->__PVT__normalizer__DOT__pool_tbl_valid 
            = (7U == (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__state));
        vlSelf->__PVT__normalizer__DOT__record_tbl_valid 
            = (7U == (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__state));
    } else {
        vlSelf->in_ready = 0U;
        vlSelf->__PVT__normalizer__DOT__record_ready = 0U;
        vlSelf->__PVT__normalizer__DOT__record_valid = 0U;
        vlSelf->__PVT__normalizer__DOT__pool_ready = 0U;
        vlSelf->__PVT__normalizer__DOT__pool_valid = 0U;
        vlSelf->__PVT__normalizer__DOT__divider_ready = 0U;
        vlSelf->__PVT__normalizer__DOT__quotient = 0U;
        vlSelf->__PVT__normalizer__DOT__remainder_value = 0U;
        vlSelf->__PVT__normalizer__DOT__class_ready = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_ready = 0U;
        vlSelf->__PVT__normalizer__DOT__divider_valid = 0U;
        vlSelf->out_valid = 0U;
        vlSelf->__PVT__normalizer__DOT__class_valid = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_valid = 0U;
        vlSelf->__PVT__normalizer__DOT__class_tbl_ready = 0U;
        vlSelf->__PVT__normalizer__DOT__pool_tbl_ready = 0U;
        vlSelf->__PVT__normalizer__DOT__record_tbl_ready = 0U;
        vlSelf->__PVT__normalizer__DOT__class_tbl_valid = 0U;
        vlSelf->__PVT__normalizer__DOT__pool_tbl_valid = 0U;
        vlSelf->__PVT__normalizer__DOT__record_tbl_valid = 0U;
    }
    vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__subtract 
        = (vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__shifted_remainder 
           >= (QData)((IData)(vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__divisor)));
    vlSelf->__PVT__normalizer__DOT__composition_equal 
        = ((IData)(__VdfgTmp_hd39cf095__0) & (vlSelf->__PVT__normalizer__DOT__record_value[1U] 
                                              == vlSelf->__PVT__normalizer__DOT__current_scalar));
    vlSelf->__PVT__normalizer__DOT__composition_before 
        = ((vlSelf->__PVT__normalizer__DOT__record_value[0U] 
            < vlSelf->__PVT__normalizer__DOT__starter_scalar) 
           | ((IData)(__VdfgTmp_hd39cf095__0) & (vlSelf->__PVT__normalizer__DOT__record_value[1U] 
                                                 < vlSelf->__PVT__normalizer__DOT__current_scalar)));
    vlSelf->__VdfgTmp_h0a1e14da__0 = (1U & ((~ (IData)(vlSelf->__PVT__normalizer__DOT__classify_selected)) 
                                            & (~ (IData)(vlSelf->__PVT__normalizer__DOT__pool_selected))));
    vlSelf->__PVT__normalizer__DOT__divider_zero = 
        ((IData)(vlSelf->__PVT__normalizer__DOT__divider_valid) 
         & (IData)(vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__zero_divisor));
    vlSelf->out_last = ((IData)(vlSelf->out_valid) 
                        & (((IData)(1U) + vlSelf->__PVT__normalizer__DOT__output_index) 
                           == vlSelf->__PVT__normalizer__DOT__scalar_count));
    vlSelf->__PVT__normalizer__DOT__class_properties 
        = (((~ (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__failed)) 
            & (IData)(vlSelf->__PVT__normalizer__DOT__class_valid))
            ? vlSelf->__PVT__normalizer__DOT__classification__DOT__property_value
            : 0U);
    if (((~ (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__failed)) 
         & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_valid))) {
        vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_data[0U] 
            = vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[0U];
        vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_data[1U] 
            = vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[1U];
        vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_data[2U] 
            = vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[2U];
        vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_data[3U] 
            = vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[3U];
    } else {
        vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_data[0U] = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_data[1U] = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_data[2U] = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_data[3U] = 0U;
    }
}

VL_ATTR_COLD void Vbench_anvil_edge_normalizer__M10___stl_sequent__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__normalization__0(Vbench_anvil_edge_normalizer__M10* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+              Vbench_anvil_edge_normalizer__M10___stl_sequent__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__normalization__0\n"); );
    // Init
    CData/*0:0*/ __VdfgTmp_hd39cf095__0;
    __VdfgTmp_hd39cf095__0 = 0;
    // Body
    vlSelf->__PVT__normalizer__DOT__record_scalar_valid 
        = ((~ ((0xd800U <= vlSelf->__PVT__normalizer__DOT__record_value[0U]) 
               & (0xdfffU >= vlSelf->__PVT__normalizer__DOT__record_value[0U]))) 
           & (0x10ffffU >= vlSelf->__PVT__normalizer__DOT__record_value[0U]));
    vlSelf->__PVT__normalizer__DOT__pool_end = (0x1ffffffffULL 
                                                & ((QData)((IData)(
                                                                   vlSelf->__PVT__normalizer__DOT__record_value[1U])) 
                                                   + (QData)((IData)(
                                                                     vlSelf->__PVT__normalizer__DOT__record_value[2U]))));
    vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__shifted_remainder 
        = (0x1ffffffffULL & (VL_SHIFTL_QQI(33,33,32, vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__remainder_work, 1U) 
                             | (QData)((IData)((vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__dividend_shift 
                                                >> 0x1fU)))));
    __VdfgTmp_hd39cf095__0 = (vlSelf->__PVT__normalizer__DOT__record_value[0U] 
                              == vlSelf->__PVT__normalizer__DOT__starter_scalar);
    vlSelf->__PVT__normalizer__DOT__classify_selected 
        = ((0xaU == (IData)(vlSelf->__PVT__normalizer__DOT__state)) 
           | (0xbU == (IData)(vlSelf->__PVT__normalizer__DOT__state)));
    vlSelf->__PVT__normalizer__DOT__pool_selected = 
        ((7U == (IData)(vlSelf->__PVT__normalizer__DOT__state)) 
         | (8U == (IData)(vlSelf->__PVT__normalizer__DOT__state)));
    if (vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) {
        vlSelf->__PVT__normalizer__DOT__record_ready 
            = (0U == (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__state));
        vlSelf->__PVT__normalizer__DOT__record_valid 
            = (0xaU == (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__state));
        vlSelf->__PVT__normalizer__DOT__pool_ready 
            = (0U == (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__state));
        vlSelf->__PVT__normalizer__DOT__pool_valid 
            = (0xaU == (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__state));
        vlSelf->__PVT__normalizer__DOT__divider_ready 
            = (0U == (IData)(vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__state));
        vlSelf->__PVT__normalizer__DOT__quotient = vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__quotient_result;
        vlSelf->__PVT__normalizer__DOT__remainder_value 
            = vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__remainder_result;
        vlSelf->__PVT__normalizer__DOT__class_ready 
            = (0U == (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__state));
        vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_ready 
            = (0U == (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state));
        vlSelf->in_ready = (1U == (IData)(vlSelf->__PVT__normalizer__DOT__state));
        vlSelf->__PVT__normalizer__DOT__divider_valid 
            = (3U == (IData)(vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__state));
        vlSelf->out_valid = (0x24U == (IData)(vlSelf->__PVT__normalizer__DOT__state));
        vlSelf->__PVT__normalizer__DOT__class_valid 
            = (6U == (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__state));
        vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_valid 
            = (0xaU == (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state));
        vlSelf->__PVT__normalizer__DOT__class_tbl_ready 
            = (8U == (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state));
        vlSelf->__PVT__normalizer__DOT__pool_tbl_ready 
            = (8U == (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__state));
        vlSelf->__PVT__normalizer__DOT__record_tbl_ready 
            = (8U == (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__state));
        vlSelf->__PVT__normalizer__DOT__class_tbl_valid 
            = (7U == (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state));
        vlSelf->__PVT__normalizer__DOT__pool_tbl_valid 
            = (7U == (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__state));
        vlSelf->__PVT__normalizer__DOT__record_tbl_valid 
            = (7U == (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__state));
    } else {
        vlSelf->__PVT__normalizer__DOT__record_ready = 0U;
        vlSelf->__PVT__normalizer__DOT__record_valid = 0U;
        vlSelf->__PVT__normalizer__DOT__pool_ready = 0U;
        vlSelf->__PVT__normalizer__DOT__pool_valid = 0U;
        vlSelf->__PVT__normalizer__DOT__divider_ready = 0U;
        vlSelf->__PVT__normalizer__DOT__quotient = 0U;
        vlSelf->__PVT__normalizer__DOT__remainder_value = 0U;
        vlSelf->__PVT__normalizer__DOT__class_ready = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_ready = 0U;
        vlSelf->in_ready = 0U;
        vlSelf->__PVT__normalizer__DOT__divider_valid = 0U;
        vlSelf->out_valid = 0U;
        vlSelf->__PVT__normalizer__DOT__class_valid = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_valid = 0U;
        vlSelf->__PVT__normalizer__DOT__class_tbl_ready = 0U;
        vlSelf->__PVT__normalizer__DOT__pool_tbl_ready = 0U;
        vlSelf->__PVT__normalizer__DOT__record_tbl_ready = 0U;
        vlSelf->__PVT__normalizer__DOT__class_tbl_valid = 0U;
        vlSelf->__PVT__normalizer__DOT__pool_tbl_valid = 0U;
        vlSelf->__PVT__normalizer__DOT__record_tbl_valid = 0U;
    }
    vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__subtract 
        = (vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__shifted_remainder 
           >= (QData)((IData)(vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__divisor)));
    vlSelf->__PVT__normalizer__DOT__composition_equal 
        = ((IData)(__VdfgTmp_hd39cf095__0) & (vlSelf->__PVT__normalizer__DOT__record_value[1U] 
                                              == vlSelf->__PVT__normalizer__DOT__current_scalar));
    vlSelf->__PVT__normalizer__DOT__composition_before 
        = ((vlSelf->__PVT__normalizer__DOT__record_value[0U] 
            < vlSelf->__PVT__normalizer__DOT__starter_scalar) 
           | ((IData)(__VdfgTmp_hd39cf095__0) & (vlSelf->__PVT__normalizer__DOT__record_value[1U] 
                                                 < vlSelf->__PVT__normalizer__DOT__current_scalar)));
    vlSelf->__VdfgTmp_h0a1e14da__0 = (1U & ((~ (IData)(vlSelf->__PVT__normalizer__DOT__classify_selected)) 
                                            & (~ (IData)(vlSelf->__PVT__normalizer__DOT__pool_selected))));
    vlSelf->__PVT__normalizer__DOT__divider_zero = 
        ((IData)(vlSelf->__PVT__normalizer__DOT__divider_valid) 
         & (IData)(vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__zero_divisor));
    vlSelf->out_last = ((IData)(vlSelf->out_valid) 
                        & (((IData)(1U) + vlSelf->__PVT__normalizer__DOT__output_index) 
                           == vlSelf->__PVT__normalizer__DOT__scalar_count));
    vlSelf->__PVT__normalizer__DOT__class_properties 
        = (((~ (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__failed)) 
            & (IData)(vlSelf->__PVT__normalizer__DOT__class_valid))
            ? vlSelf->__PVT__normalizer__DOT__classification__DOT__property_value
            : 0U);
    if (((~ (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__failed)) 
         & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_valid))) {
        vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_data[0U] 
            = vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[0U];
        vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_data[1U] 
            = vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[1U];
        vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_data[2U] 
            = vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[2U];
        vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_data[3U] 
            = vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[3U];
    } else {
        vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_data[0U] = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_data[1U] = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_data[2U] = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_data[3U] = 0U;
    }
}
