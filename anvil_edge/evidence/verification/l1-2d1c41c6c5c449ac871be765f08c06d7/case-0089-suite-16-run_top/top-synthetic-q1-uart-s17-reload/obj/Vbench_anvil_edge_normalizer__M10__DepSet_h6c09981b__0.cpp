// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vbench.h for the primary calling header

#include "Vbench__pch.h"
#include "Vbench__Syms.h"
#include "Vbench_anvil_edge_normalizer__M10.h"

VL_INLINE_OPT void Vbench_anvil_edge_normalizer__M10___act_comb__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalization__0(Vbench_anvil_edge_normalizer__M10* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+              Vbench_anvil_edge_normalizer__M10___act_comb__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalization__0\n"); );
    // Body
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

VL_INLINE_OPT void Vbench_anvil_edge_normalizer__M10___nba_sequent__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalization__0(Vbench_anvil_edge_normalizer__M10* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+              Vbench_anvil_edge_normalizer__M10___nba_sequent__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalization__0\n"); );
    // Init
    CData/*0:0*/ __VdfgTmp_hd39cf095__0;
    __VdfgTmp_hd39cf095__0 = 0;
    CData/*5:0*/ __Vdly__normalizer__DOT__state;
    __Vdly__normalizer__DOT__state = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__mode;
    __Vdly__normalizer__DOT__mode = 0;
    QData/*63:0*/ __Vdly__normalizer__DOT__decomposition_base;
    __Vdly__normalizer__DOT__decomposition_base = 0;
    QData/*63:0*/ __Vdly__normalizer__DOT__scalar_pool_base;
    __Vdly__normalizer__DOT__scalar_pool_base = 0;
    QData/*63:0*/ __Vdly__normalizer__DOT__composition_base;
    __Vdly__normalizer__DOT__composition_base = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__decomposition_count;
    __Vdly__normalizer__DOT__decomposition_count = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__scalar_pool_count;
    __Vdly__normalizer__DOT__scalar_pool_count = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__composition_count;
    __Vdly__normalizer__DOT__composition_count = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__scalar_count;
    __Vdly__normalizer__DOT__scalar_count = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__output_index;
    __Vdly__normalizer__DOT__output_index = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__composite_scalar;
    __Vdly__normalizer__DOT__composite_scalar = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__hangul_product;
    __Vdly__normalizer__DOT__hangul_product = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__read_index;
    __Vdly__normalizer__DOT__read_index = 0;
    CData/*3:0*/ __Vdlyvdim0__normalizer__DOT__scalars__v0;
    __Vdlyvdim0__normalizer__DOT__scalars__v0 = 0;
    IData/*31:0*/ __Vdlyvval__normalizer__DOT__scalars__v0;
    __Vdlyvval__normalizer__DOT__scalars__v0 = 0;
    CData/*0:0*/ __Vdlyvset__normalizer__DOT__scalars__v0;
    __Vdlyvset__normalizer__DOT__scalars__v0 = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__starter_scalar;
    __Vdly__normalizer__DOT__starter_scalar = 0;
    CData/*3:0*/ __Vdlyvdim0__normalizer__DOT__scalars__v1;
    __Vdlyvdim0__normalizer__DOT__scalars__v1 = 0;
    IData/*31:0*/ __Vdlyvval__normalizer__DOT__scalars__v1;
    __Vdlyvval__normalizer__DOT__scalars__v1 = 0;
    CData/*0:0*/ __Vdlyvset__normalizer__DOT__scalars__v1;
    __Vdlyvset__normalizer__DOT__scalars__v1 = 0;
    CData/*7:0*/ __Vdly__normalizer__DOT__last_ccc;
    __Vdly__normalizer__DOT__last_ccc = 0;
    CData/*3:0*/ __Vdlyvdim0__normalizer__DOT__combining_classes__v0;
    __Vdlyvdim0__normalizer__DOT__combining_classes__v0 = 0;
    CData/*7:0*/ __Vdlyvval__normalizer__DOT__combining_classes__v0;
    __Vdlyvval__normalizer__DOT__combining_classes__v0 = 0;
    CData/*0:0*/ __Vdlyvset__normalizer__DOT__combining_classes__v0;
    __Vdlyvset__normalizer__DOT__combining_classes__v0 = 0;
    CData/*0:0*/ __Vdly__normalizer__DOT__starter_valid;
    __Vdly__normalizer__DOT__starter_valid = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__write_index;
    __Vdly__normalizer__DOT__write_index = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__search_low;
    __Vdly__normalizer__DOT__search_low = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__search_high;
    __Vdly__normalizer__DOT__search_high = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__search_middle;
    __Vdly__normalizer__DOT__search_middle = 0;
    CData/*0:0*/ __Vdly__normalizer__DOT__reading_composition;
    __Vdly__normalizer__DOT__reading_composition = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__hangul_v;
    __Vdly__normalizer__DOT__hangul_v = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__hangul_t;
    __Vdly__normalizer__DOT__hangul_t = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__append_scalar;
    __Vdly__normalizer__DOT__append_scalar = 0;
    CData/*1:0*/ __Vdly__normalizer__DOT__append_source;
    __Vdly__normalizer__DOT__append_source = 0;
    CData/*1:0*/ __Vdly__normalizer__DOT__hangul_part;
    __Vdly__normalizer__DOT__hangul_part = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__pool_cursor;
    __Vdly__normalizer__DOT__pool_cursor = 0;
    CData/*3:0*/ __Vdlyvdim0__normalizer__DOT__scalars__v2;
    __Vdlyvdim0__normalizer__DOT__scalars__v2 = 0;
    IData/*31:0*/ __Vdlyvval__normalizer__DOT__scalars__v2;
    __Vdlyvval__normalizer__DOT__scalars__v2 = 0;
    CData/*0:0*/ __Vdlyvset__normalizer__DOT__scalars__v2;
    __Vdlyvset__normalizer__DOT__scalars__v2 = 0;
    CData/*3:0*/ __Vdlyvdim0__normalizer__DOT__combining_classes__v1;
    __Vdlyvdim0__normalizer__DOT__combining_classes__v1 = 0;
    CData/*7:0*/ __Vdlyvval__normalizer__DOT__combining_classes__v1;
    __Vdlyvval__normalizer__DOT__combining_classes__v1 = 0;
    CData/*3:0*/ __Vdlyvdim0__normalizer__DOT__scalars__v3;
    __Vdlyvdim0__normalizer__DOT__scalars__v3 = 0;
    IData/*31:0*/ __Vdlyvval__normalizer__DOT__scalars__v3;
    __Vdlyvval__normalizer__DOT__scalars__v3 = 0;
    CData/*0:0*/ __Vdlyvset__normalizer__DOT__scalars__v3;
    __Vdlyvset__normalizer__DOT__scalars__v3 = 0;
    CData/*3:0*/ __Vdlyvdim0__normalizer__DOT__combining_classes__v2;
    __Vdlyvdim0__normalizer__DOT__combining_classes__v2 = 0;
    CData/*7:0*/ __Vdlyvval__normalizer__DOT__combining_classes__v2;
    __Vdlyvval__normalizer__DOT__combining_classes__v2 = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__insert_position;
    __Vdly__normalizer__DOT__insert_position = 0;
    CData/*3:0*/ __Vdly__normalizer__DOT__records__DOT__reader__DOT__state;
    __Vdly__normalizer__DOT__records__DOT__reader__DOT__state = 0;
    VlWide<3>/*65:0*/ __Vdly__normalizer__DOT__records__DOT__reader__DOT__offset_value;
    VL_ZERO_W(66, __Vdly__normalizer__DOT__records__DOT__reader__DOT__offset_value);
    CData/*3:0*/ __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state;
    __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state = 0;
    VlWide<3>/*65:0*/ __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value;
    VL_ZERO_W(66, __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value);
    CData/*0:0*/ __Vdly__normalizer__DOT__classification__DOT__failed;
    __Vdly__normalizer__DOT__classification__DOT__failed = 0;
    CData/*7:0*/ __Vdly__normalizer__DOT__classification__DOT__code;
    __Vdly__normalizer__DOT__classification__DOT__code = 0;
    CData/*3:0*/ __Vdly__normalizer__DOT__classification__DOT__state;
    __Vdly__normalizer__DOT__classification__DOT__state = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__classification__DOT__high_index;
    __Vdly__normalizer__DOT__classification__DOT__high_index = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__classification__DOT__low_index;
    __Vdly__normalizer__DOT__classification__DOT__low_index = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__classification__DOT__middle;
    __Vdly__normalizer__DOT__classification__DOT__middle = 0;
    QData/*63:0*/ __Vdly__normalizer__DOT__classification__DOT__base;
    __Vdly__normalizer__DOT__classification__DOT__base = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__classification__DOT__range_count;
    __Vdly__normalizer__DOT__classification__DOT__range_count = 0;
    CData/*3:0*/ __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state;
    __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 0;
    VlWide<3>/*65:0*/ __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value;
    VL_ZERO_W(66, __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value);
    CData/*1:0*/ __Vdly__normalizer__DOT__hangul_divider__DOT__divider__DOT__state;
    __Vdly__normalizer__DOT__hangul_divider__DOT__divider__DOT__state = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__hangul_divider__DOT__divider__DOT__quotient_work;
    __Vdly__normalizer__DOT__hangul_divider__DOT__divider__DOT__quotient_work = 0;
    VlWide<3>/*95:0*/ __Vtemp_5;
    VlWide<3>/*95:0*/ __Vtemp_6;
    VlWide<3>/*95:0*/ __Vtemp_8;
    VlWide<3>/*95:0*/ __Vtemp_10;
    VlWide<3>/*95:0*/ __Vtemp_11;
    VlWide<3>/*95:0*/ __Vtemp_12;
    VlWide<3>/*95:0*/ __Vtemp_14;
    VlWide<3>/*95:0*/ __Vtemp_15;
    VlWide<3>/*95:0*/ __Vtemp_16;
    VlWide<3>/*95:0*/ __Vtemp_18;
    VlWide<3>/*95:0*/ __Vtemp_19;
    VlWide<3>/*95:0*/ __Vtemp_25;
    VlWide<3>/*95:0*/ __Vtemp_26;
    VlWide<3>/*95:0*/ __Vtemp_28;
    VlWide<3>/*95:0*/ __Vtemp_30;
    VlWide<3>/*95:0*/ __Vtemp_31;
    VlWide<3>/*95:0*/ __Vtemp_32;
    VlWide<3>/*95:0*/ __Vtemp_34;
    VlWide<3>/*95:0*/ __Vtemp_35;
    VlWide<3>/*95:0*/ __Vtemp_36;
    VlWide<3>/*95:0*/ __Vtemp_38;
    VlWide<3>/*95:0*/ __Vtemp_39;
    VlWide<3>/*95:0*/ __Vtemp_42;
    VlWide<3>/*95:0*/ __Vtemp_43;
    VlWide<3>/*95:0*/ __Vtemp_45;
    VlWide<3>/*95:0*/ __Vtemp_47;
    VlWide<3>/*95:0*/ __Vtemp_48;
    VlWide<3>/*95:0*/ __Vtemp_49;
    VlWide<3>/*95:0*/ __Vtemp_51;
    VlWide<3>/*95:0*/ __Vtemp_52;
    VlWide<3>/*95:0*/ __Vtemp_53;
    VlWide<3>/*95:0*/ __Vtemp_55;
    VlWide<3>/*95:0*/ __Vtemp_56;
    // Body
    __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[0U] 
        = vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[0U];
    __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[1U] 
        = vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[1U];
    __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[2U] 
        = vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[2U];
    __Vdly__normalizer__DOT__records__DOT__reader__DOT__offset_value[0U] 
        = vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__offset_value[0U];
    __Vdly__normalizer__DOT__records__DOT__reader__DOT__offset_value[1U] 
        = vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__offset_value[1U];
    __Vdly__normalizer__DOT__records__DOT__reader__DOT__offset_value[2U] 
        = vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__offset_value[2U];
    __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state 
        = vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state;
    __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value[0U] 
        = vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value[0U];
    __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value[1U] 
        = vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value[1U];
    __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value[2U] 
        = vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value[2U];
    __Vdly__normalizer__DOT__records__DOT__reader__DOT__state 
        = vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__state;
    __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state 
        = vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__state;
    __Vdly__normalizer__DOT__insert_position = vlSelf->__PVT__normalizer__DOT__insert_position;
    __Vdly__normalizer__DOT__pool_cursor = vlSelf->__PVT__normalizer__DOT__pool_cursor;
    __Vdly__normalizer__DOT__hangul_part = vlSelf->__PVT__normalizer__DOT__hangul_part;
    __Vdly__normalizer__DOT__append_source = vlSelf->__PVT__normalizer__DOT__append_source;
    __Vdly__normalizer__DOT__append_scalar = vlSelf->__PVT__normalizer__DOT__append_scalar;
    __Vdly__normalizer__DOT__hangul_t = vlSelf->__PVT__normalizer__DOT__hangul_t;
    __Vdly__normalizer__DOT__hangul_v = vlSelf->__PVT__normalizer__DOT__hangul_v;
    __Vdly__normalizer__DOT__reading_composition = vlSelf->__PVT__normalizer__DOT__reading_composition;
    __Vdly__normalizer__DOT__search_middle = vlSelf->__PVT__normalizer__DOT__search_middle;
    __Vdly__normalizer__DOT__search_high = vlSelf->__PVT__normalizer__DOT__search_high;
    __Vdly__normalizer__DOT__search_low = vlSelf->__PVT__normalizer__DOT__search_low;
    __Vdly__normalizer__DOT__write_index = vlSelf->__PVT__normalizer__DOT__write_index;
    __Vdly__normalizer__DOT__starter_valid = vlSelf->__PVT__normalizer__DOT__starter_valid;
    __Vdly__normalizer__DOT__last_ccc = vlSelf->__PVT__normalizer__DOT__last_ccc;
    __Vdly__normalizer__DOT__read_index = vlSelf->__PVT__normalizer__DOT__read_index;
    __Vdly__normalizer__DOT__hangul_product = vlSelf->__PVT__normalizer__DOT__hangul_product;
    __Vdly__normalizer__DOT__composite_scalar = vlSelf->__PVT__normalizer__DOT__composite_scalar;
    __Vdly__normalizer__DOT__composition_count = vlSelf->__PVT__normalizer__DOT__composition_count;
    __Vdly__normalizer__DOT__scalar_pool_count = vlSelf->__PVT__normalizer__DOT__scalar_pool_count;
    __Vdly__normalizer__DOT__decomposition_count = vlSelf->__PVT__normalizer__DOT__decomposition_count;
    __Vdly__normalizer__DOT__composition_base = vlSelf->__PVT__normalizer__DOT__composition_base;
    __Vdly__normalizer__DOT__scalar_pool_base = vlSelf->__PVT__normalizer__DOT__scalar_pool_base;
    __Vdly__normalizer__DOT__decomposition_base = vlSelf->__PVT__normalizer__DOT__decomposition_base;
    __Vdly__normalizer__DOT__mode = vlSelf->__PVT__normalizer__DOT__mode;
    __Vdly__normalizer__DOT__output_index = vlSelf->__PVT__normalizer__DOT__output_index;
    __Vdly__normalizer__DOT__scalar_count = vlSelf->__PVT__normalizer__DOT__scalar_count;
    __Vdlyvset__normalizer__DOT__combining_classes__v0 = 0U;
    __Vdlyvset__normalizer__DOT__scalars__v0 = 0U;
    __Vdlyvset__normalizer__DOT__scalars__v1 = 0U;
    __Vdly__normalizer__DOT__starter_scalar = vlSelf->__PVT__normalizer__DOT__starter_scalar;
    __Vdlyvset__normalizer__DOT__scalars__v2 = 0U;
    __Vdlyvset__normalizer__DOT__scalars__v3 = 0U;
    __Vdly__normalizer__DOT__state = vlSelf->__PVT__normalizer__DOT__state;
    __Vdly__normalizer__DOT__hangul_divider__DOT__divider__DOT__quotient_work 
        = vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__quotient_work;
    __Vdly__normalizer__DOT__hangul_divider__DOT__divider__DOT__state 
        = vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__state;
    __Vdly__normalizer__DOT__classification__DOT__range_count 
        = vlSelf->__PVT__normalizer__DOT__classification__DOT__range_count;
    __Vdly__normalizer__DOT__classification__DOT__base 
        = vlSelf->__PVT__normalizer__DOT__classification__DOT__base;
    __Vdly__normalizer__DOT__classification__DOT__middle 
        = vlSelf->__PVT__normalizer__DOT__classification__DOT__middle;
    __Vdly__normalizer__DOT__classification__DOT__low_index 
        = vlSelf->__PVT__normalizer__DOT__classification__DOT__low_index;
    __Vdly__normalizer__DOT__classification__DOT__high_index 
        = vlSelf->__PVT__normalizer__DOT__classification__DOT__high_index;
    __Vdly__normalizer__DOT__classification__DOT__code 
        = vlSelf->__PVT__normalizer__DOT__classification__DOT__code;
    __Vdly__normalizer__DOT__classification__DOT__failed 
        = vlSelf->__PVT__normalizer__DOT__classification__DOT__failed;
    __Vdly__normalizer__DOT__classification__DOT__state 
        = vlSelf->__PVT__normalizer__DOT__classification__DOT__state;
    if (vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) {
        if ((8U & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__state))) {
            __Vdly__normalizer__DOT__classification__DOT__failed = 1U;
            __Vdly__normalizer__DOT__classification__DOT__code = 0x12U;
            __Vdly__normalizer__DOT__classification__DOT__state = 6U;
        } else if ((4U & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__state))) {
            if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__state))) {
                    __Vdly__normalizer__DOT__classification__DOT__failed = 1U;
                    __Vdly__normalizer__DOT__classification__DOT__code = 0x12U;
                    __Vdly__normalizer__DOT__classification__DOT__state = 6U;
                } else if (((IData)(vlSelf->__PVT__normalizer__DOT__class_valid) 
                            & ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                               & (0xbU == (IData)(vlSelf->__PVT__normalizer__DOT__state))))) {
                    __Vdly__normalizer__DOT__classification__DOT__state = 0U;
                }
            } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__state))) {
                if ((((((vlSelf->__PVT__normalizer__DOT__classification__DOT__first_scalar 
                         > vlSelf->__PVT__normalizer__DOT__classification__DOT__last_scalar) 
                        | (0x10ffffU < vlSelf->__PVT__normalizer__DOT__classification__DOT__last_scalar)) 
                       | ((0xdfffU >= vlSelf->__PVT__normalizer__DOT__classification__DOT__first_scalar) 
                          & (0xd800U <= vlSelf->__PVT__normalizer__DOT__classification__DOT__last_scalar))) 
                      | (vlSelf->__PVT__normalizer__DOT__classification__DOT__class_value 
                         >= vlSelf->__PVT__normalizer__DOT__classification__DOT__class_count)) 
                     | (0U != (vlSelf->__PVT__normalizer__DOT__classification__DOT__property_value 
                               >> 0xaU)))) {
                    __Vdly__normalizer__DOT__classification__DOT__failed = 1U;
                    __Vdly__normalizer__DOT__classification__DOT__code = 0x12U;
                    __Vdly__normalizer__DOT__classification__DOT__state = 6U;
                } else if ((vlSelf->__PVT__normalizer__DOT__classification__DOT__scalar 
                            < vlSelf->__PVT__normalizer__DOT__classification__DOT__first_scalar)) {
                    __Vdly__normalizer__DOT__classification__DOT__high_index 
                        = vlSelf->__PVT__normalizer__DOT__classification__DOT__middle;
                    __Vdly__normalizer__DOT__classification__DOT__state = 2U;
                } else if ((vlSelf->__PVT__normalizer__DOT__classification__DOT__scalar 
                            > vlSelf->__PVT__normalizer__DOT__classification__DOT__last_scalar)) {
                    __Vdly__normalizer__DOT__classification__DOT__low_index 
                        = ((IData)(1U) + vlSelf->__PVT__normalizer__DOT__classification__DOT__middle);
                    __Vdly__normalizer__DOT__classification__DOT__state = 2U;
                } else {
                    __Vdly__normalizer__DOT__classification__DOT__state = 6U;
                }
            } else if (vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_valid) {
                if (((IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_valid) 
                     & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__failed))) {
                    __Vdly__normalizer__DOT__classification__DOT__failed = 1U;
                    __Vdly__normalizer__DOT__classification__DOT__code 
                        = ((IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_valid)
                            ? (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__code)
                            : 0U);
                    __Vdly__normalizer__DOT__classification__DOT__state = 6U;
                } else {
                    vlSelf->__PVT__normalizer__DOT__classification__DOT__first_scalar 
                        = vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_data[0U];
                    vlSelf->__PVT__normalizer__DOT__classification__DOT__last_scalar 
                        = vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_data[1U];
                    vlSelf->__PVT__normalizer__DOT__classification__DOT__class_value 
                        = vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_data[2U];
                    vlSelf->__PVT__normalizer__DOT__classification__DOT__property_value 
                        = vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_data[3U];
                    __Vdly__normalizer__DOT__classification__DOT__state = 5U;
                }
            }
        } else if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__state))) {
            if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__state))) {
                if (vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_ready) {
                    __Vdly__normalizer__DOT__classification__DOT__state = 4U;
                }
            } else if ((vlSelf->__PVT__normalizer__DOT__classification__DOT__low_index 
                        >= vlSelf->__PVT__normalizer__DOT__classification__DOT__high_index)) {
                __Vdly__normalizer__DOT__classification__DOT__failed = 1U;
                __Vdly__normalizer__DOT__classification__DOT__code = 0x12U;
                __Vdly__normalizer__DOT__classification__DOT__state = 6U;
            } else {
                __Vdly__normalizer__DOT__classification__DOT__middle 
                    = (vlSelf->__PVT__normalizer__DOT__classification__DOT__low_index 
                       + VL_SHIFTR_III(32,32,32, (vlSelf->__PVT__normalizer__DOT__classification__DOT__high_index 
                                                  - vlSelf->__PVT__normalizer__DOT__classification__DOT__low_index), 1U));
                __Vdly__normalizer__DOT__classification__DOT__state = 3U;
            }
        } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__state))) {
            if (((0x10ffffU < vlSelf->__PVT__normalizer__DOT__classification__DOT__scalar) 
                 | ((0xd800U <= vlSelf->__PVT__normalizer__DOT__classification__DOT__scalar) 
                    & (0xdfffU >= vlSelf->__PVT__normalizer__DOT__classification__DOT__scalar)))) {
                __Vdly__normalizer__DOT__classification__DOT__failed = 1U;
                __Vdly__normalizer__DOT__classification__DOT__code = 0x10U;
                __Vdly__normalizer__DOT__classification__DOT__state = 6U;
            } else if ((1U & ((((~ (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__admitted)) 
                                | (0U == vlSelf->__PVT__normalizer__DOT__classification__DOT__range_count)) 
                               | (0U == vlSelf->__PVT__normalizer__DOT__classification__DOT__class_count)) 
                              | (0U != (3U & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__base)))))) {
                __Vdly__normalizer__DOT__classification__DOT__failed = 1U;
                __Vdly__normalizer__DOT__classification__DOT__code = 6U;
                __Vdly__normalizer__DOT__classification__DOT__state = 6U;
            } else {
                __Vdly__normalizer__DOT__classification__DOT__state = 2U;
            }
        } else if ((((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                     & (0xaU == (IData)(vlSelf->__PVT__normalizer__DOT__state))) 
                    & (IData)(vlSelf->__PVT__normalizer__DOT__class_ready))) {
            vlSelf->__PVT__normalizer__DOT__classification__DOT__admitted = 1U;
            __Vdly__normalizer__DOT__classification__DOT__base 
                = vlSelf->__PVT__normalizer__DOT__ranges_base;
            __Vdly__normalizer__DOT__classification__DOT__range_count 
                = vlSelf->__PVT__normalizer__DOT__range_count;
            vlSelf->__PVT__normalizer__DOT__classification__DOT__class_count 
                = vlSelf->__PVT__normalizer__DOT__class_count;
            vlSelf->__PVT__normalizer__DOT__classification__DOT__scalar 
                = vlSelf->__PVT__normalizer__DOT__append_scalar;
            __Vdly__normalizer__DOT__classification__DOT__low_index = 0U;
            __Vdly__normalizer__DOT__classification__DOT__high_index 
                = vlSelf->__PVT__normalizer__DOT__range_count;
            __Vdly__normalizer__DOT__classification__DOT__failed = 0U;
            __Vdly__normalizer__DOT__classification__DOT__code = 0U;
            vlSelf->__PVT__normalizer__DOT__classification__DOT__class_value = 0U;
            vlSelf->__PVT__normalizer__DOT__classification__DOT__property_value = 0U;
            __Vdly__normalizer__DOT__classification__DOT__state = 1U;
        }
        if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__state))) {
            if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__state))) {
                if (((IData)(vlSelf->__PVT__normalizer__DOT__divider_valid) 
                     & ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                        & ((0x12U == (IData)(vlSelf->__PVT__normalizer__DOT__state)) 
                           | ((0x14U == (IData)(vlSelf->__PVT__normalizer__DOT__state)) 
                              | (0x23U == (IData)(vlSelf->__PVT__normalizer__DOT__state))))))) {
                    __Vdly__normalizer__DOT__hangul_divider__DOT__divider__DOT__state = 0U;
                }
            } else {
                if (vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__zero_divisor) {
                    vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__quotient_result = 0U;
                    vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__remainder_result = 0U;
                } else {
                    vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__quotient_result 
                        = vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__quotient_work;
                    vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__remainder_result 
                        = (IData)(vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__remainder_work);
                }
                __Vdly__normalizer__DOT__hangul_divider__DOT__divider__DOT__state = 3U;
            }
        } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__state))) {
            vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__dividend_shift 
                = VL_SHIFTL_III(32,32,32, vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__dividend_shift, 1U);
            if (vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__subtract) {
                __Vdly__normalizer__DOT__hangul_divider__DOT__divider__DOT__quotient_work 
                    = (1U | VL_SHIFTL_III(32,32,32, vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__quotient_work, 1U));
                vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__remainder_work 
                    = (0x1ffffffffULL & (vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__shifted_remainder 
                                         - (QData)((IData)(vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__divisor))));
            } else {
                __Vdly__normalizer__DOT__hangul_divider__DOT__divider__DOT__quotient_work 
                    = VL_SHIFTL_III(32,32,32, vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__quotient_work, 1U);
                vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__remainder_work 
                    = vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__shifted_remainder;
            }
            if ((0x1fU == (IData)(vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__iterations))) {
                __Vdly__normalizer__DOT__hangul_divider__DOT__divider__DOT__state = 2U;
            } else {
                vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__iterations 
                    = (0x3fU & ((IData)(1U) + (IData)(vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__iterations)));
            }
        } else if ((((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                     & ((0x11U == (IData)(vlSelf->__PVT__normalizer__DOT__state)) 
                        | ((0x13U == (IData)(vlSelf->__PVT__normalizer__DOT__state)) 
                           | (0x22U == (IData)(vlSelf->__PVT__normalizer__DOT__state))))) 
                    & (IData)(vlSelf->__PVT__normalizer__DOT__divider_ready))) {
            vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__dividend_shift 
                = ((0x22U == (IData)(vlSelf->__PVT__normalizer__DOT__state))
                    ? (vlSelf->__PVT__normalizer__DOT__starter_scalar 
                       - (IData)(0xac00U)) : vlSelf->__PVT__normalizer__DOT__hangul_index);
            __Vdly__normalizer__DOT__hangul_divider__DOT__divider__DOT__quotient_work = 0U;
            vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__iterations = 0U;
            vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__divisor 
                = ((0x11U == (IData)(vlSelf->__PVT__normalizer__DOT__state))
                    ? 0x24cU : 0x1cU);
            vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__remainder_work = 0ULL;
            vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__zero_divisor 
                = (0U == ((0x11U == (IData)(vlSelf->__PVT__normalizer__DOT__state))
                           ? 0x24cU : 0x1cU));
            __Vdly__normalizer__DOT__hangul_divider__DOT__divider__DOT__state = 1U;
        }
        if ((8U & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
            if ((4U & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
                vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__failed = 1U;
                vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__code = 0x11U;
                __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 0xaU;
            } else if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
                    vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__failed = 1U;
                    vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__code = 0x11U;
                    __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 0xaU;
                } else if (((IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_valid) 
                            & ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                               & (4U == (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__state))))) {
                    __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 0U;
                }
            } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
                VL_ASSIGNSEL_WI(128,32,(0x7fU & VL_SHIFTL_III(7,32,32, (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__word_index), 5U)), vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data, vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__read_data);
                if ((3U == (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__word_index))) {
                    __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 0xaU;
                } else {
                    vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__word_index 
                        = (3U & ((IData)(1U) + (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__word_index)));
                    __Vtemp_5[0U] = 4U;
                    __Vtemp_5[1U] = 0U;
                    __Vtemp_5[2U] = 0U;
                    VL_ADD_W(3, __Vtemp_6, __Vtemp_5, vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value);
                    __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[0U] 
                        = __Vtemp_6[0U];
                    __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[1U] 
                        = __Vtemp_6[1U];
                    __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[2U] 
                        = (3U & __Vtemp_6[2U]);
                    __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 5U;
                }
            } else if ((((IData)(vlSelf->__PVT__normalizer__DOT__classify_selected) 
                         & (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__tbl_rsp_valid)) 
                        & (IData)(vlSelf->__PVT__normalizer__DOT__class_tbl_ready))) {
                if (vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer_rsp_error) {
                    vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__failed = 1U;
                    vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__code = 4U;
                    __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 0xaU;
                } else {
                    vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__read_data 
                        = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer_rsp_data;
                    __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 9U;
                }
            }
        } else if ((4U & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
            if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
                    if (((IData)(vlSelf->__PVT__normalizer__DOT__class_tbl_valid) 
                         & ((IData)(vlSelf->__PVT__normalizer__DOT__classify_selected) 
                            & (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__tbl_req_ready)))) {
                        __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 8U;
                    }
                } else if ((IData)(((0U != vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__request_address[2U]) 
                                    | VL_GTE_W(3, vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__request_address, vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__table_end)))) {
                    vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__failed = 1U;
                    vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__code = 0x11U;
                    __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 0xaU;
                } else {
                    __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 7U;
                }
            } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
                VL_ADD_W(3, __Vtemp_8, vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__data_start, vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value);
                vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__request_address[0U] 
                    = __Vtemp_8[0U];
                vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__request_address[1U] 
                    = __Vtemp_8[1U];
                vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__request_address[2U] 
                    = (3U & __Vtemp_8[2U]);
                __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 6U;
            } else if ((IData)(((((0ULL != (3ULL & vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__base)) 
                                  | (0U != vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__data_start[2U])) 
                                 | (0U != vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__table_end[2U])) 
                                | ((0U == vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__count) 
                                   | (vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__index 
                                      >= vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__count))))) {
                vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__failed = 1U;
                vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__code = 0x11U;
                __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 0xaU;
            } else {
                __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 5U;
            }
        } else if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
            if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
                __Vtemp_10[0U] = vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__count;
                __Vtemp_10[1U] = 0U;
                __Vtemp_10[2U] = 0U;
                VL_SHIFTL_WWI(66,66,32, __Vtemp_11, __Vtemp_10, 4U);
                VL_ADD_W(3, __Vtemp_12, vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__data_start, __Vtemp_11);
                vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__table_end[0U] 
                    = __Vtemp_12[0U];
                vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__table_end[1U] 
                    = __Vtemp_12[1U];
                vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__table_end[2U] 
                    = (3U & __Vtemp_12[2U]);
                __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 4U;
            } else {
                __Vtemp_14[0U] = 0x20U;
                __Vtemp_14[1U] = 0U;
                __Vtemp_14[2U] = 0U;
                __Vtemp_15[0U] = (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__base);
                __Vtemp_15[1U] = (IData)((vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__base 
                                          >> 0x20U));
                __Vtemp_15[2U] = 0U;
                VL_ADD_W(3, __Vtemp_16, __Vtemp_14, __Vtemp_15);
                vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__data_start[0U] 
                    = __Vtemp_16[0U];
                vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__data_start[1U] 
                    = __Vtemp_16[1U];
                vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__data_start[2U] 
                    = (3U & __Vtemp_16[2U]);
                __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 3U;
            }
        } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
            __Vtemp_18[0U] = vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__index;
            __Vtemp_18[1U] = 0U;
            __Vtemp_18[2U] = 0U;
            VL_SHIFTL_WWI(66,66,32, __Vtemp_19, __Vtemp_18, 4U);
            __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[0U] 
                = __Vtemp_19[0U];
            __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[1U] 
                = __Vtemp_19[1U];
            __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[2U] 
                = (3U & __Vtemp_19[2U]);
            __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 2U;
        } else if ((((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                     & (3U == (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__state))) 
                    & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_ready))) {
            vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__word_index = 0U;
            vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__base 
                = vlSelf->__PVT__normalizer__DOT__classification__DOT__base;
            vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__count 
                = vlSelf->__PVT__normalizer__DOT__classification__DOT__range_count;
            vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__index 
                = vlSelf->__PVT__normalizer__DOT__classification__DOT__middle;
            vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[0U] = 0U;
            vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[1U] = 0U;
            vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[2U] = 0U;
            vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[3U] = 0U;
            vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__failed = 0U;
            vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__code = 0U;
            __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 1U;
        }
        if ((0x20U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
            if ((0x10U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                vlSelf->__PVT__normalizer__DOT__code = 0x12U;
                __Vdly__normalizer__DOT__state = 0x26U;
            } else if ((8U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                vlSelf->__PVT__normalizer__DOT__code = 0x12U;
                __Vdly__normalizer__DOT__state = 0x26U;
            } else if ((4U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                    if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                        vlSelf->__PVT__normalizer__DOT__code = 0x12U;
                        __Vdly__normalizer__DOT__state = 0x26U;
                    } else {
                        __Vdly__normalizer__DOT__state = 0x26U;
                    }
                } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                    if (vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__start) {
                        if ((1U & (((~ (IData)(vlSymsp->TOP.bench__DOT__boot_done)) 
                                    | (4U < ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__loader_done)
                                              ? vlSymsp->TOP.bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[3U]
                                              : 0U))) 
                                   | ((0U != ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__loader_done)
                                               ? vlSymsp->TOP.bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[3U]
                                               : 0U)) 
                                      & ((((((0U == vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_range_count) 
                                             | (0U 
                                                == vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_class_count)) 
                                            | (0U != 
                                               (3U 
                                                & (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_ranges_base)))) 
                                           | (0U != 
                                              (3U & (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_decomposition_base)))) 
                                          | (0U != 
                                             (3U & (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_scalar_pool_base)))) 
                                         | (0U != (3U 
                                                   & (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_composition_base)))))))) {
                            vlSelf->__PVT__normalizer__DOT__code = 6U;
                            __Vdly__normalizer__DOT__state = 0x26U;
                        } else {
                            __Vdly__normalizer__DOT__mode 
                                = ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__loader_done)
                                    ? vlSymsp->TOP.bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[3U]
                                    : 0U);
                            vlSelf->__PVT__normalizer__DOT__ranges_base 
                                = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_ranges_base;
                            __Vdly__normalizer__DOT__decomposition_base 
                                = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_decomposition_base;
                            __Vdly__normalizer__DOT__scalar_pool_base 
                                = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_scalar_pool_base;
                            __Vdly__normalizer__DOT__composition_base 
                                = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_composition_base;
                            vlSelf->__PVT__normalizer__DOT__range_count 
                                = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_range_count;
                            vlSelf->__PVT__normalizer__DOT__class_count 
                                = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_class_count;
                            __Vdly__normalizer__DOT__decomposition_count 
                                = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_decomposition_count;
                            __Vdly__normalizer__DOT__scalar_pool_count 
                                = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_scalar_pool_count;
                            __Vdly__normalizer__DOT__composition_count 
                                = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_composition_count;
                            __Vdly__normalizer__DOT__scalar_count = 0U;
                            __Vdly__normalizer__DOT__output_index = 0U;
                            vlSelf->__PVT__normalizer__DOT__code = 0U;
                            __Vdly__normalizer__DOT__state = 1U;
                        }
                    }
                } else if (((IData)(vlSelf->out_valid) 
                            & ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____VdfgTmp_h67e2c008__0) 
                               & (IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalized_specials.in_ready)))) {
                    if (vlSelf->out_last) {
                        __Vdly__normalizer__DOT__state = 0x25U;
                    } else {
                        __Vdly__normalizer__DOT__output_index 
                            = ((IData)(1U) + vlSelf->__PVT__normalizer__DOT__output_index);
                    }
                }
            } else if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                    if (vlSelf->__PVT__normalizer__DOT__divider_valid) {
                        if (vlSelf->__PVT__normalizer__DOT__divider_zero) {
                            vlSelf->__PVT__normalizer__DOT__code = 0x12U;
                            __Vdly__normalizer__DOT__state = 0x26U;
                        } else if ((0U == vlSelf->__PVT__normalizer__DOT__remainder_value)) {
                            __Vdly__normalizer__DOT__composite_scalar 
                                = (vlSelf->__PVT__normalizer__DOT__starter_scalar 
                                   + (vlSelf->__PVT__normalizer__DOT__current_scalar 
                                      - (IData)(0x11a7U)));
                            __Vdly__normalizer__DOT__state = 0x1cU;
                        } else {
                            __Vdly__normalizer__DOT__state = 0x18U;
                        }
                    }
                } else if (vlSelf->__PVT__normalizer__DOT__divider_ready) {
                    __Vdly__normalizer__DOT__state = 0x23U;
                }
            } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                __Vdly__normalizer__DOT__composite_scalar 
                    = ((IData)(0xac00U) + vlSelf->__PVT__normalizer__DOT__hangul_product);
                __Vdly__normalizer__DOT__state = 0x1cU;
            } else {
                __Vdly__normalizer__DOT__hangul_product 
                    = (VL_SHIFTL_III(32,32,32, vlSelf->__PVT__normalizer__DOT__hangul_product, 5U) 
                       - VL_SHIFTL_III(32,32,32, vlSelf->__PVT__normalizer__DOT__hangul_product, 2U));
                __Vdly__normalizer__DOT__state = 0x21U;
            }
        } else if ((0x10U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
            if ((8U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                if ((4U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                    if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                        if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                            __Vdly__normalizer__DOT__hangul_product 
                                = (vlSelf->__PVT__normalizer__DOT__hangul_product 
                                   + vlSelf->__PVT__normalizer__DOT__hangul_v_index);
                            __Vdly__normalizer__DOT__state = 0x20U;
                        } else {
                            __Vdly__normalizer__DOT__hangul_product 
                                = (vlSelf->__PVT__normalizer__DOT__hangul_product 
                                   + vlSelf->__PVT__normalizer__DOT__hangul_l_index);
                            __Vdly__normalizer__DOT__state = 0x1fU;
                        }
                    } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                        __Vdly__normalizer__DOT__hangul_product 
                            = (VL_SHIFTL_III(32,32,32, vlSelf->__PVT__normalizer__DOT__hangul_l_index, 4U) 
                               + VL_SHIFTL_III(32,32,32, vlSelf->__PVT__normalizer__DOT__hangul_l_index, 2U));
                        __Vdly__normalizer__DOT__state = 0x1eU;
                    } else {
                        __Vdly__normalizer__DOT__read_index 
                            = ((IData)(1U) + vlSelf->__PVT__normalizer__DOT__read_index);
                        __Vdlyvval__normalizer__DOT__scalars__v0 
                            = vlSelf->__PVT__normalizer__DOT__composite_scalar;
                        __Vdlyvset__normalizer__DOT__scalars__v0 = 1U;
                        __Vdlyvdim0__normalizer__DOT__scalars__v0 
                            = (0xfU & vlSelf->__PVT__normalizer__DOT__starter_position);
                        __Vdly__normalizer__DOT__state = 0x16U;
                        __Vdly__normalizer__DOT__starter_scalar 
                            = vlSelf->__PVT__normalizer__DOT__composite_scalar;
                    }
                } else if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                    if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                        __Vdly__normalizer__DOT__read_index 
                            = ((IData)(1U) + vlSelf->__PVT__normalizer__DOT__read_index);
                        __Vdlyvval__normalizer__DOT__scalars__v1 
                            = vlSelf->__PVT__normalizer__DOT__current_scalar;
                        __Vdlyvset__normalizer__DOT__scalars__v1 = 1U;
                        __Vdlyvdim0__normalizer__DOT__scalars__v1 
                            = (0xfU & vlSelf->__PVT__normalizer__DOT__write_index);
                        __Vdly__normalizer__DOT__last_ccc 
                            = vlSelf->__PVT__normalizer__DOT__current_ccc;
                        __Vdly__normalizer__DOT__state = 0x16U;
                        __Vdlyvval__normalizer__DOT__combining_classes__v0 
                            = vlSelf->__PVT__normalizer__DOT__current_ccc;
                        __Vdlyvset__normalizer__DOT__combining_classes__v0 = 1U;
                        __Vdlyvdim0__normalizer__DOT__combining_classes__v0 
                            = (0xfU & vlSelf->__PVT__normalizer__DOT__write_index);
                        if ((0U == (IData)(vlSelf->__PVT__normalizer__DOT__current_ccc))) {
                            __Vdly__normalizer__DOT__starter_valid = 1U;
                            __Vdly__normalizer__DOT__starter_scalar 
                                = vlSelf->__PVT__normalizer__DOT__current_scalar;
                            vlSelf->__PVT__normalizer__DOT__starter_position 
                                = vlSelf->__PVT__normalizer__DOT__write_index;
                        }
                        __Vdly__normalizer__DOT__write_index 
                            = ((IData)(1U) + vlSelf->__PVT__normalizer__DOT__write_index);
                    } else if ((1U & ((((((~ (IData)(vlSelf->__PVT__normalizer__DOT__record_scalar_valid)) 
                                          | (0x10ffffU 
                                             < vlSelf->__PVT__normalizer__DOT__record_value[1U])) 
                                         | ((0xd800U 
                                             <= vlSelf->__PVT__normalizer__DOT__record_value[1U]) 
                                            & (0xdfffU 
                                               >= vlSelf->__PVT__normalizer__DOT__record_value[1U]))) 
                                        | (0x10ffffU 
                                           < vlSelf->__PVT__normalizer__DOT__record_value[2U])) 
                                       | ((0xd800U 
                                           <= vlSelf->__PVT__normalizer__DOT__record_value[2U]) 
                                          & (0xdfffU 
                                             >= vlSelf->__PVT__normalizer__DOT__record_value[2U]))) 
                                      | (0U != vlSelf->__PVT__normalizer__DOT__record_value[3U])))) {
                        vlSelf->__PVT__normalizer__DOT__code = 0x12U;
                        __Vdly__normalizer__DOT__state = 0x26U;
                    } else if (vlSelf->__PVT__normalizer__DOT__composition_equal) {
                        __Vdly__normalizer__DOT__composite_scalar 
                            = vlSelf->__PVT__normalizer__DOT__record_value[2U];
                        __Vdly__normalizer__DOT__state = 0x1cU;
                    } else {
                        if (vlSelf->__PVT__normalizer__DOT__composition_before) {
                            __Vdly__normalizer__DOT__search_low 
                                = ((IData)(1U) + vlSelf->__PVT__normalizer__DOT__search_middle);
                        } else {
                            __Vdly__normalizer__DOT__search_high 
                                = vlSelf->__PVT__normalizer__DOT__search_middle;
                        }
                        __Vdly__normalizer__DOT__state = 0x19U;
                    }
                } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                    if ((vlSelf->__PVT__normalizer__DOT__search_low 
                         >= vlSelf->__PVT__normalizer__DOT__search_high)) {
                        __Vdly__normalizer__DOT__state = 0x1bU;
                    } else {
                        __Vdly__normalizer__DOT__search_middle 
                            = (vlSelf->__PVT__normalizer__DOT__search_low 
                               + VL_SHIFTR_III(32,32,32, 
                                               (vlSelf->__PVT__normalizer__DOT__search_high 
                                                - vlSelf->__PVT__normalizer__DOT__search_low), 1U));
                        __Vdly__normalizer__DOT__state = 4U;
                    }
                } else {
                    __Vdly__normalizer__DOT__search_low = 0U;
                    __Vdly__normalizer__DOT__search_high 
                        = vlSelf->__PVT__normalizer__DOT__composition_count;
                    __Vdly__normalizer__DOT__reading_composition = 1U;
                    __Vdly__normalizer__DOT__state = 0x19U;
                }
            } else if ((4U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                    if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                        if ((1U & ((~ (IData)(vlSelf->__PVT__normalizer__DOT__starter_valid)) 
                                   | (~ ((0U == (IData)(vlSelf->__PVT__normalizer__DOT__last_ccc)) 
                                         | ((IData)(vlSelf->__PVT__normalizer__DOT__last_ccc) 
                                            < (IData)(vlSelf->__PVT__normalizer__DOT__current_ccc))))))) {
                            __Vdly__normalizer__DOT__state = 0x1bU;
                        } else if (((((0x1100U <= vlSelf->__PVT__normalizer__DOT__starter_scalar) 
                                      & (0x1112U >= vlSelf->__PVT__normalizer__DOT__starter_scalar)) 
                                     & (0x1161U <= vlSelf->__PVT__normalizer__DOT__current_scalar)) 
                                    & (0x1175U >= vlSelf->__PVT__normalizer__DOT__current_scalar))) {
                            vlSelf->__PVT__normalizer__DOT__hangul_l_index 
                                = (vlSelf->__PVT__normalizer__DOT__starter_scalar 
                                   - (IData)(0x1100U));
                            vlSelf->__PVT__normalizer__DOT__hangul_v_index 
                                = (vlSelf->__PVT__normalizer__DOT__current_scalar 
                                   - (IData)(0x1161U));
                            __Vdly__normalizer__DOT__state = 0x1dU;
                        } else {
                            __Vdly__normalizer__DOT__state 
                                = (((((0xac00U <= vlSelf->__PVT__normalizer__DOT__starter_scalar) 
                                      & (0xd7a3U >= vlSelf->__PVT__normalizer__DOT__starter_scalar)) 
                                     & (0x11a7U < vlSelf->__PVT__normalizer__DOT__current_scalar)) 
                                    & (0x11c2U >= vlSelf->__PVT__normalizer__DOT__current_scalar))
                                    ? 0x22U : 0x18U);
                        }
                    } else if ((vlSelf->__PVT__normalizer__DOT__read_index 
                                == vlSelf->__PVT__normalizer__DOT__scalar_count)) {
                        __Vdly__normalizer__DOT__scalar_count 
                            = vlSelf->__PVT__normalizer__DOT__write_index;
                        __Vdly__normalizer__DOT__output_index = 0U;
                        __Vdly__normalizer__DOT__state = 0x24U;
                    } else {
                        vlSelf->__PVT__normalizer__DOT__current_scalar 
                            = vlSelf->__PVT__normalizer__DOT__scalars
                            [(0xfU & vlSelf->__PVT__normalizer__DOT__read_index)];
                        __Vdly__normalizer__DOT__state = 0x17U;
                        vlSelf->__PVT__normalizer__DOT__current_ccc 
                            = vlSelf->__PVT__normalizer__DOT__combining_classes
                            [(0xfU & vlSelf->__PVT__normalizer__DOT__read_index)];
                    }
                } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                    __Vdly__normalizer__DOT__read_index = 0U;
                    __Vdly__normalizer__DOT__write_index = 0U;
                    __Vdly__normalizer__DOT__starter_valid = 0U;
                    __Vdly__normalizer__DOT__last_ccc = 0U;
                    __Vdly__normalizer__DOT__state = 0x16U;
                } else if (vlSelf->__PVT__normalizer__DOT__divider_valid) {
                    if (vlSelf->__PVT__normalizer__DOT__divider_zero) {
                        vlSelf->__PVT__normalizer__DOT__code = 0x12U;
                        __Vdly__normalizer__DOT__state = 0x26U;
                    } else {
                        __Vdly__normalizer__DOT__hangul_v 
                            = ((IData)(0x1161U) + vlSelf->__PVT__normalizer__DOT__quotient);
                        __Vdly__normalizer__DOT__hangul_t 
                            = ((IData)(0x11a7U) + vlSelf->__PVT__normalizer__DOT__remainder_value);
                        __Vdly__normalizer__DOT__append_scalar 
                            = vlSelf->__PVT__normalizer__DOT__hangul_l;
                        __Vdly__normalizer__DOT__append_source = 2U;
                        __Vdly__normalizer__DOT__hangul_part = 0U;
                        __Vdly__normalizer__DOT__state = 9U;
                    }
                }
            } else if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                    if (vlSelf->__PVT__normalizer__DOT__divider_ready) {
                        __Vdly__normalizer__DOT__state = 0x14U;
                    }
                } else if (vlSelf->__PVT__normalizer__DOT__divider_valid) {
                    if (vlSelf->__PVT__normalizer__DOT__divider_zero) {
                        vlSelf->__PVT__normalizer__DOT__code = 0x12U;
                        __Vdly__normalizer__DOT__state = 0x26U;
                    } else {
                        vlSelf->__PVT__normalizer__DOT__hangul_l 
                            = ((IData)(0x1100U) + vlSelf->__PVT__normalizer__DOT__quotient);
                        vlSelf->__PVT__normalizer__DOT__hangul_index 
                            = vlSelf->__PVT__normalizer__DOT__remainder_value;
                        __Vdly__normalizer__DOT__state = 0x13U;
                    }
                }
            } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                if (vlSelf->__PVT__normalizer__DOT__divider_ready) {
                    __Vdly__normalizer__DOT__state = 0x12U;
                }
            } else if (vlSelf->__PVT__normalizer__DOT__input_last) {
                if (((1U == vlSelf->__PVT__normalizer__DOT__mode) 
                     | (2U == vlSelf->__PVT__normalizer__DOT__mode))) {
                    __Vdly__normalizer__DOT__state = 0x15U;
                } else {
                    __Vdly__normalizer__DOT__output_index = 0U;
                    __Vdly__normalizer__DOT__state = 0x24U;
                }
            } else {
                __Vdly__normalizer__DOT__state = 1U;
            }
        } else if ((8U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
            if ((4U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                    if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                        if (((1U == (IData)(vlSelf->__PVT__normalizer__DOT__append_source)) 
                             & (1U < vlSelf->__PVT__normalizer__DOT__pool_remaining))) {
                            __Vdly__normalizer__DOT__pool_cursor 
                                = ((IData)(1U) + vlSelf->__PVT__normalizer__DOT__pool_cursor);
                            vlSelf->__PVT__normalizer__DOT__pool_remaining 
                                = (vlSelf->__PVT__normalizer__DOT__pool_remaining 
                                   - (IData)(1U));
                            __Vdly__normalizer__DOT__state = 7U;
                        } else if (((2U == (IData)(vlSelf->__PVT__normalizer__DOT__append_source)) 
                                    & (0U == (IData)(vlSelf->__PVT__normalizer__DOT__hangul_part)))) {
                            __Vdly__normalizer__DOT__append_scalar 
                                = vlSelf->__PVT__normalizer__DOT__hangul_v;
                            __Vdly__normalizer__DOT__hangul_part = 1U;
                            __Vdly__normalizer__DOT__state = 9U;
                        } else if ((((2U == (IData)(vlSelf->__PVT__normalizer__DOT__append_source)) 
                                     & (1U == (IData)(vlSelf->__PVT__normalizer__DOT__hangul_part))) 
                                    & (0x11a7U != vlSelf->__PVT__normalizer__DOT__hangul_t))) {
                            __Vdly__normalizer__DOT__append_scalar 
                                = vlSelf->__PVT__normalizer__DOT__hangul_t;
                            __Vdly__normalizer__DOT__hangul_part = 2U;
                            __Vdly__normalizer__DOT__state = 9U;
                        } else {
                            __Vdly__normalizer__DOT__state = 0x10U;
                        }
                    } else {
                        __Vdlyvval__normalizer__DOT__scalars__v2 
                            = vlSelf->__PVT__normalizer__DOT__append_scalar;
                        __Vdlyvset__normalizer__DOT__scalars__v2 = 1U;
                        __Vdlyvdim0__normalizer__DOT__scalars__v2 
                            = (0xfU & vlSelf->__PVT__normalizer__DOT__insert_position);
                        __Vdlyvval__normalizer__DOT__combining_classes__v1 
                            = vlSelf->__PVT__normalizer__DOT__append_ccc;
                        __Vdlyvdim0__normalizer__DOT__combining_classes__v1 
                            = (0xfU & vlSelf->__PVT__normalizer__DOT__insert_position);
                        __Vdly__normalizer__DOT__state = 0xfU;
                    }
                } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                    if (((IData)(vlSelf->__PVT__normalizer__DOT__previous_ccc) 
                         > (IData)(vlSelf->__PVT__normalizer__DOT__append_ccc))) {
                        __Vdlyvval__normalizer__DOT__scalars__v3 
                            = vlSelf->__PVT__normalizer__DOT__previous_scalar;
                        __Vdlyvset__normalizer__DOT__scalars__v3 = 1U;
                        __Vdlyvdim0__normalizer__DOT__scalars__v3 
                            = (0xfU & vlSelf->__PVT__normalizer__DOT__insert_position);
                        __Vdlyvval__normalizer__DOT__combining_classes__v2 
                            = vlSelf->__PVT__normalizer__DOT__previous_ccc;
                        __Vdlyvdim0__normalizer__DOT__combining_classes__v2 
                            = (0xfU & vlSelf->__PVT__normalizer__DOT__insert_position);
                        __Vdly__normalizer__DOT__insert_position 
                            = (vlSelf->__PVT__normalizer__DOT__insert_position 
                               - (IData)(1U));
                        __Vdly__normalizer__DOT__state 
                            = ((1U == vlSelf->__PVT__normalizer__DOT__insert_position)
                                ? 0xeU : 0xcU);
                    } else {
                        __Vdly__normalizer__DOT__state = 0xeU;
                    }
                } else {
                    vlSelf->__PVT__normalizer__DOT__previous_scalar 
                        = vlSelf->__PVT__normalizer__DOT__scalars
                        [(0xfU & (vlSelf->__PVT__normalizer__DOT__insert_position 
                                  - (IData)(1U)))];
                    __Vdly__normalizer__DOT__state = 0xdU;
                    vlSelf->__PVT__normalizer__DOT__previous_ccc 
                        = vlSelf->__PVT__normalizer__DOT__combining_classes
                        [(0xfU & (vlSelf->__PVT__normalizer__DOT__insert_position 
                                  - (IData)(1U)))];
                }
            } else if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                    if (vlSelf->__PVT__normalizer__DOT__class_valid) {
                        if (((IData)(vlSelf->__PVT__normalizer__DOT__class_valid) 
                             & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__failed))) {
                            vlSelf->__PVT__normalizer__DOT__code 
                                = ((IData)(vlSelf->__PVT__normalizer__DOT__class_valid)
                                    ? (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__code)
                                    : 0U);
                            __Vdly__normalizer__DOT__state = 0x26U;
                        } else {
                            vlSelf->__PVT__normalizer__DOT__append_ccc 
                                = (0xffU & vlSelf->__PVT__normalizer__DOT__class_properties);
                            __Vdly__normalizer__DOT__insert_position 
                                = vlSelf->__PVT__normalizer__DOT__scalar_count;
                            __Vdly__normalizer__DOT__scalar_count 
                                = ((IData)(1U) + vlSelf->__PVT__normalizer__DOT__scalar_count);
                            __Vdly__normalizer__DOT__state 
                                = (((0U == vlSelf->__PVT__normalizer__DOT__scalar_count) 
                                    | (0U == (0xffU 
                                              & vlSelf->__PVT__normalizer__DOT__class_properties)))
                                    ? 0xeU : 0xcU);
                        }
                    }
                } else if (vlSelf->__PVT__normalizer__DOT__class_ready) {
                    __Vdly__normalizer__DOT__state = 0xbU;
                }
            } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                if (((0x10ffffU < vlSelf->__PVT__normalizer__DOT__append_scalar) 
                     | ((0xd800U <= vlSelf->__PVT__normalizer__DOT__append_scalar) 
                        & (0xdfffU >= vlSelf->__PVT__normalizer__DOT__append_scalar)))) {
                    vlSelf->__PVT__normalizer__DOT__code = 0x12U;
                    __Vdly__normalizer__DOT__state = 0x26U;
                } else if ((0x10U <= vlSelf->__PVT__normalizer__DOT__scalar_count)) {
                    vlSelf->__PVT__normalizer__DOT__code = 0x30U;
                    __Vdly__normalizer__DOT__state = 0x26U;
                } else if ((0U == vlSelf->__PVT__normalizer__DOT__mode)) {
                    vlSelf->__PVT__normalizer__DOT__append_ccc = 0U;
                    __Vdly__normalizer__DOT__insert_position 
                        = vlSelf->__PVT__normalizer__DOT__scalar_count;
                    __Vdly__normalizer__DOT__state = 0xeU;
                    __Vdly__normalizer__DOT__scalar_count 
                        = ((IData)(1U) + vlSelf->__PVT__normalizer__DOT__scalar_count);
                } else {
                    __Vdly__normalizer__DOT__state = 0xaU;
                }
            } else if (vlSelf->__PVT__normalizer__DOT__pool_valid) {
                if (((IData)(vlSelf->__PVT__normalizer__DOT__pool_valid) 
                     & (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__failed))) {
                    vlSelf->__PVT__normalizer__DOT__code 
                        = ((IData)(vlSelf->__PVT__normalizer__DOT__pool_valid)
                            ? (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__code)
                            : 0U);
                    __Vdly__normalizer__DOT__state = 0x26U;
                } else {
                    __Vdly__normalizer__DOT__append_scalar 
                        = (((~ (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__failed)) 
                            & (IData)(vlSelf->__PVT__normalizer__DOT__pool_valid))
                            ? vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__result_data
                            : 0U);
                    __Vdly__normalizer__DOT__state = 9U;
                }
            }
        } else if ((4U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
            if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                    if (vlSelf->__PVT__normalizer__DOT__pool_ready) {
                        __Vdly__normalizer__DOT__state = 8U;
                    }
                } else if ((1U & (((((~ (IData)(vlSelf->__PVT__normalizer__DOT__record_scalar_valid)) 
                                     | (0U != (vlSelf->__PVT__normalizer__DOT__record_value[3U] 
                                               >> 1U))) 
                                    | (0U == vlSelf->__PVT__normalizer__DOT__record_value[2U])) 
                                   | (IData)((vlSelf->__PVT__normalizer__DOT__pool_end 
                                              >> 0x20U))) 
                                  | (vlSelf->__PVT__normalizer__DOT__pool_end 
                                     > (QData)((IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool_count)))))) {
                    vlSelf->__PVT__normalizer__DOT__code = 0x12U;
                    __Vdly__normalizer__DOT__state = 0x26U;
                } else if ((vlSelf->__PVT__normalizer__DOT__record_value[0U] 
                            < vlSelf->__PVT__normalizer__DOT__input_scalar)) {
                    __Vdly__normalizer__DOT__search_low 
                        = ((IData)(1U) + vlSelf->__PVT__normalizer__DOT__search_middle);
                    __Vdly__normalizer__DOT__state = 3U;
                } else if ((vlSelf->__PVT__normalizer__DOT__record_value[0U] 
                            > vlSelf->__PVT__normalizer__DOT__input_scalar)) {
                    __Vdly__normalizer__DOT__search_high 
                        = vlSelf->__PVT__normalizer__DOT__search_middle;
                    __Vdly__normalizer__DOT__state = 3U;
                } else if ((vlSelf->__PVT__normalizer__DOT__record_value[3U] 
                            & ((1U == vlSelf->__PVT__normalizer__DOT__mode) 
                               | (3U == vlSelf->__PVT__normalizer__DOT__mode)))) {
                    __Vdly__normalizer__DOT__append_scalar 
                        = vlSelf->__PVT__normalizer__DOT__input_scalar;
                    __Vdly__normalizer__DOT__append_source = 0U;
                    __Vdly__normalizer__DOT__state = 9U;
                } else {
                    __Vdly__normalizer__DOT__pool_cursor 
                        = vlSelf->__PVT__normalizer__DOT__record_value[1U];
                    vlSelf->__PVT__normalizer__DOT__pool_remaining 
                        = vlSelf->__PVT__normalizer__DOT__record_value[2U];
                    __Vdly__normalizer__DOT__append_source = 1U;
                    __Vdly__normalizer__DOT__state = 7U;
                }
            } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                if (vlSelf->__PVT__normalizer__DOT__record_valid) {
                    if (((IData)(vlSelf->__PVT__normalizer__DOT__record_valid) 
                         & (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__failed))) {
                        vlSelf->__PVT__normalizer__DOT__code 
                            = ((IData)(vlSelf->__PVT__normalizer__DOT__record_valid)
                                ? (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__code)
                                : 0U);
                        __Vdly__normalizer__DOT__state = 0x26U;
                    } else {
                        if (((~ (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__failed)) 
                             & (IData)(vlSelf->__PVT__normalizer__DOT__record_valid))) {
                            vlSelf->__PVT__normalizer__DOT__record_value[0U] 
                                = vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__result_data[0U];
                            vlSelf->__PVT__normalizer__DOT__record_value[1U] 
                                = vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__result_data[1U];
                            vlSelf->__PVT__normalizer__DOT__record_value[2U] 
                                = vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__result_data[2U];
                            vlSelf->__PVT__normalizer__DOT__record_value[3U] 
                                = vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__result_data[3U];
                        } else {
                            vlSelf->__PVT__normalizer__DOT__record_value[0U] = 0U;
                            vlSelf->__PVT__normalizer__DOT__record_value[1U] = 0U;
                            vlSelf->__PVT__normalizer__DOT__record_value[2U] = 0U;
                            vlSelf->__PVT__normalizer__DOT__record_value[3U] = 0U;
                        }
                        __Vdly__normalizer__DOT__state 
                            = ((IData)(vlSelf->__PVT__normalizer__DOT__reading_composition)
                                ? 0x1aU : 6U);
                    }
                }
            } else if (vlSelf->__PVT__normalizer__DOT__record_ready) {
                __Vdly__normalizer__DOT__state = 5U;
            }
        } else if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
            if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                if ((vlSelf->__PVT__normalizer__DOT__search_low 
                     >= vlSelf->__PVT__normalizer__DOT__search_high)) {
                    __Vdly__normalizer__DOT__append_scalar 
                        = vlSelf->__PVT__normalizer__DOT__input_scalar;
                    __Vdly__normalizer__DOT__append_source = 0U;
                    __Vdly__normalizer__DOT__state = 9U;
                } else {
                    __Vdly__normalizer__DOT__search_middle 
                        = (vlSelf->__PVT__normalizer__DOT__search_low 
                           + VL_SHIFTR_III(32,32,32, 
                                           (vlSelf->__PVT__normalizer__DOT__search_high 
                                            - vlSelf->__PVT__normalizer__DOT__search_low), 1U));
                    __Vdly__normalizer__DOT__state = 4U;
                }
            } else {
                __Vdly__normalizer__DOT__search_low = 0U;
                __Vdly__normalizer__DOT__search_high 
                    = vlSelf->__PVT__normalizer__DOT__decomposition_count;
                __Vdly__normalizer__DOT__reading_composition = 0U;
                __Vdly__normalizer__DOT__state = 3U;
            }
        } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
            if ((((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                  & ((7U == (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__state)) 
                     & (IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__raw_specials.out_valid))) 
                 & (IData)(vlSelf->in_ready))) {
                if (((0x10ffffU < vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__raw_specials.out_value) 
                     | ((0xd800U <= vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__raw_specials.out_value) 
                        & (0xdfffU >= vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__raw_specials.out_value)))) {
                    vlSelf->__PVT__normalizer__DOT__code = 0x10U;
                    __Vdly__normalizer__DOT__state = 0x26U;
                } else {
                    vlSelf->__PVT__normalizer__DOT__input_scalar 
                        = vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__raw_specials.out_value;
                    vlSelf->__PVT__normalizer__DOT__input_last 
                        = vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__raw_specials.out_boundary;
                    __Vdly__normalizer__DOT__append_source = 0U;
                    __Vdly__normalizer__DOT__append_scalar 
                        = vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__raw_specials.out_value;
                    if ((0U == vlSelf->__PVT__normalizer__DOT__mode)) {
                        __Vdly__normalizer__DOT__state = 9U;
                    } else if (((0xac00U <= vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__raw_specials.out_value) 
                                & (0xd7a3U >= vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__raw_specials.out_value))) {
                        vlSelf->__PVT__normalizer__DOT__hangul_index 
                            = (vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__raw_specials.out_value 
                               - (IData)(0xac00U));
                        __Vdly__normalizer__DOT__state = 0x11U;
                    } else {
                        __Vdly__normalizer__DOT__state = 2U;
                    }
                }
            }
        } else if (vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__start) {
            if ((1U & (((~ (IData)(vlSymsp->TOP.bench__DOT__boot_done)) 
                        | (4U < ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__loader_done)
                                  ? vlSymsp->TOP.bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[3U]
                                  : 0U))) | ((0U != 
                                              ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__loader_done)
                                                ? vlSymsp->TOP.bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[3U]
                                                : 0U)) 
                                             & ((((((0U 
                                                     == vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_range_count) 
                                                    | (0U 
                                                       == vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_class_count)) 
                                                   | (0U 
                                                      != 
                                                      (3U 
                                                       & (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_ranges_base)))) 
                                                  | (0U 
                                                     != 
                                                     (3U 
                                                      & (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_decomposition_base)))) 
                                                 | (0U 
                                                    != 
                                                    (3U 
                                                     & (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_scalar_pool_base)))) 
                                                | (0U 
                                                   != 
                                                   (3U 
                                                    & (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_composition_base)))))))) {
                vlSelf->__PVT__normalizer__DOT__code = 6U;
                __Vdly__normalizer__DOT__state = 0x26U;
            } else {
                __Vdly__normalizer__DOT__mode = ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__loader_done)
                                                  ? 
                                                 vlSymsp->TOP.bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[3U]
                                                  : 0U);
                vlSelf->__PVT__normalizer__DOT__ranges_base 
                    = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_ranges_base;
                __Vdly__normalizer__DOT__decomposition_base 
                    = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_decomposition_base;
                __Vdly__normalizer__DOT__scalar_pool_base 
                    = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_scalar_pool_base;
                __Vdly__normalizer__DOT__composition_base 
                    = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_composition_base;
                vlSelf->__PVT__normalizer__DOT__range_count 
                    = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_range_count;
                vlSelf->__PVT__normalizer__DOT__class_count 
                    = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_class_count;
                __Vdly__normalizer__DOT__decomposition_count 
                    = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_decomposition_count;
                __Vdly__normalizer__DOT__scalar_pool_count 
                    = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_scalar_pool_count;
                __Vdly__normalizer__DOT__composition_count 
                    = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_composition_count;
                __Vdly__normalizer__DOT__scalar_count = 0U;
                __Vdly__normalizer__DOT__output_index = 0U;
                vlSelf->__PVT__normalizer__DOT__code = 0U;
                __Vdly__normalizer__DOT__state = 1U;
            }
        }
        if ((8U & (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__state))) {
            if ((4U & (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__state))) {
                vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__failed = 1U;
                vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__code = 0x11U;
                __Vdly__normalizer__DOT__records__DOT__reader__DOT__state = 0xaU;
            } else if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__state))) {
                    vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__failed = 1U;
                    vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__code = 0x11U;
                    __Vdly__normalizer__DOT__records__DOT__reader__DOT__state = 0xaU;
                } else if (((IData)(vlSelf->__PVT__normalizer__DOT__record_valid) 
                            & ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                               & (5U == (IData)(vlSelf->__PVT__normalizer__DOT__state))))) {
                    __Vdly__normalizer__DOT__records__DOT__reader__DOT__state = 0U;
                }
            } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__state))) {
                VL_ASSIGNSEL_WI(128,32,(0x7fU & VL_SHIFTL_III(7,32,32, (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__word_index), 5U)), vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__result_data, vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__read_data);
                if ((3U == (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__word_index))) {
                    __Vdly__normalizer__DOT__records__DOT__reader__DOT__state = 0xaU;
                } else {
                    vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__word_index 
                        = (3U & ((IData)(1U) + (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__word_index)));
                    __Vtemp_25[0U] = 4U;
                    __Vtemp_25[1U] = 0U;
                    __Vtemp_25[2U] = 0U;
                    VL_ADD_W(3, __Vtemp_26, __Vtemp_25, vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__offset_value);
                    __Vdly__normalizer__DOT__records__DOT__reader__DOT__offset_value[0U] 
                        = __Vtemp_26[0U];
                    __Vdly__normalizer__DOT__records__DOT__reader__DOT__offset_value[1U] 
                        = __Vtemp_26[1U];
                    __Vdly__normalizer__DOT__records__DOT__reader__DOT__offset_value[2U] 
                        = (3U & __Vtemp_26[2U]);
                    __Vdly__normalizer__DOT__records__DOT__reader__DOT__state = 5U;
                }
            } else if ((((IData)(vlSelf->__VdfgTmp_h0a1e14da__0) 
                         & (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__tbl_rsp_valid)) 
                        & (IData)(vlSelf->__PVT__normalizer__DOT__record_tbl_ready))) {
                if (vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer_rsp_error) {
                    vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__failed = 1U;
                    vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__code = 4U;
                    __Vdly__normalizer__DOT__records__DOT__reader__DOT__state = 0xaU;
                } else {
                    vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__read_data 
                        = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer_rsp_data;
                    __Vdly__normalizer__DOT__records__DOT__reader__DOT__state = 9U;
                }
            }
        } else if ((4U & (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__state))) {
            if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__state))) {
                    if (((IData)(vlSelf->__PVT__normalizer__DOT__record_tbl_valid) 
                         & ((IData)(vlSelf->__VdfgTmp_h0a1e14da__0) 
                            & (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__tbl_req_ready)))) {
                        __Vdly__normalizer__DOT__records__DOT__reader__DOT__state = 8U;
                    }
                } else if ((IData)(((0U != vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__request_address[2U]) 
                                    | VL_GTE_W(3, vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__request_address, vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__table_end)))) {
                    vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__failed = 1U;
                    vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__code = 0x11U;
                    __Vdly__normalizer__DOT__records__DOT__reader__DOT__state = 0xaU;
                } else {
                    __Vdly__normalizer__DOT__records__DOT__reader__DOT__state = 7U;
                }
            } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__state))) {
                VL_ADD_W(3, __Vtemp_28, vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__data_start, vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__offset_value);
                vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__request_address[0U] 
                    = __Vtemp_28[0U];
                vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__request_address[1U] 
                    = __Vtemp_28[1U];
                vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__request_address[2U] 
                    = (3U & __Vtemp_28[2U]);
                __Vdly__normalizer__DOT__records__DOT__reader__DOT__state = 6U;
            } else if ((IData)(((((0ULL != (3ULL & vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__base)) 
                                  | (0U != vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__data_start[2U])) 
                                 | (0U != vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__table_end[2U])) 
                                | ((0U == vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__count) 
                                   | (vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__index 
                                      >= vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__count))))) {
                vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__failed = 1U;
                vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__code = 0x11U;
                __Vdly__normalizer__DOT__records__DOT__reader__DOT__state = 0xaU;
            } else {
                __Vdly__normalizer__DOT__records__DOT__reader__DOT__state = 5U;
            }
        } else if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__state))) {
            if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__state))) {
                __Vtemp_30[0U] = vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__count;
                __Vtemp_30[1U] = 0U;
                __Vtemp_30[2U] = 0U;
                VL_SHIFTL_WWI(66,66,32, __Vtemp_31, __Vtemp_30, 4U);
                VL_ADD_W(3, __Vtemp_32, vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__data_start, __Vtemp_31);
                vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__table_end[0U] 
                    = __Vtemp_32[0U];
                vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__table_end[1U] 
                    = __Vtemp_32[1U];
                vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__table_end[2U] 
                    = (3U & __Vtemp_32[2U]);
                __Vdly__normalizer__DOT__records__DOT__reader__DOT__state = 4U;
            } else {
                __Vtemp_34[0U] = 0x20U;
                __Vtemp_34[1U] = 0U;
                __Vtemp_34[2U] = 0U;
                __Vtemp_35[0U] = (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__base);
                __Vtemp_35[1U] = (IData)((vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__base 
                                          >> 0x20U));
                __Vtemp_35[2U] = 0U;
                VL_ADD_W(3, __Vtemp_36, __Vtemp_34, __Vtemp_35);
                vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__data_start[0U] 
                    = __Vtemp_36[0U];
                vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__data_start[1U] 
                    = __Vtemp_36[1U];
                vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__data_start[2U] 
                    = (3U & __Vtemp_36[2U]);
                __Vdly__normalizer__DOT__records__DOT__reader__DOT__state = 3U;
            }
        } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__state))) {
            __Vtemp_38[0U] = vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__index;
            __Vtemp_38[1U] = 0U;
            __Vtemp_38[2U] = 0U;
            VL_SHIFTL_WWI(66,66,32, __Vtemp_39, __Vtemp_38, 4U);
            __Vdly__normalizer__DOT__records__DOT__reader__DOT__offset_value[0U] 
                = __Vtemp_39[0U];
            __Vdly__normalizer__DOT__records__DOT__reader__DOT__offset_value[1U] 
                = __Vtemp_39[1U];
            __Vdly__normalizer__DOT__records__DOT__reader__DOT__offset_value[2U] 
                = (3U & __Vtemp_39[2U]);
            __Vdly__normalizer__DOT__records__DOT__reader__DOT__state = 2U;
        } else if ((((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                     & (4U == (IData)(vlSelf->__PVT__normalizer__DOT__state))) 
                    & (IData)(vlSelf->__PVT__normalizer__DOT__record_ready))) {
            vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__word_index = 0U;
            if (vlSelf->__PVT__normalizer__DOT__reading_composition) {
                vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__base 
                    = vlSelf->__PVT__normalizer__DOT__composition_base;
                vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__count 
                    = vlSelf->__PVT__normalizer__DOT__composition_count;
            } else {
                vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__base 
                    = vlSelf->__PVT__normalizer__DOT__decomposition_base;
                vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__count 
                    = vlSelf->__PVT__normalizer__DOT__decomposition_count;
            }
            vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__index 
                = vlSelf->__PVT__normalizer__DOT__search_middle;
            vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__result_data[0U] = 0U;
            vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__result_data[1U] = 0U;
            vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__result_data[2U] = 0U;
            vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__result_data[3U] = 0U;
            vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__failed = 0U;
            vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__code = 0U;
            __Vdly__normalizer__DOT__records__DOT__reader__DOT__state = 1U;
        }
        if ((8U & (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__state))) {
            if ((4U & (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__state))) {
                vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__failed = 1U;
                vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__code = 0x11U;
                __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state = 0xaU;
            } else if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__state))) {
                    vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__failed = 1U;
                    vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__code = 0x11U;
                    __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state = 0xaU;
                } else if (((IData)(vlSelf->__PVT__normalizer__DOT__pool_valid) 
                            & ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                               & (8U == (IData)(vlSelf->__PVT__normalizer__DOT__state))))) {
                    __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state = 0U;
                }
            } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__state))) {
                vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__result_data 
                    = (((~ ((IData)(0xffffffffU) << 
                            (0x1fU & VL_SHIFTL_III(5,32,32, (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__word_index), 5U)))) 
                        & vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__result_data) 
                       | (0xffffffffULL & (vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__read_data 
                                           << (0x1fU 
                                               & VL_SHIFTL_III(5,32,32, (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__word_index), 5U)))));
                if (vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__word_index) {
                    vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__word_index 
                        = (1U & ((IData)(1U) + (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__word_index)));
                    __Vtemp_42[0U] = 4U;
                    __Vtemp_42[1U] = 0U;
                    __Vtemp_42[2U] = 0U;
                    VL_ADD_W(3, __Vtemp_43, __Vtemp_42, vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value);
                    __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value[0U] 
                        = __Vtemp_43[0U];
                    __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value[1U] 
                        = __Vtemp_43[1U];
                    __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value[2U] 
                        = (3U & __Vtemp_43[2U]);
                    __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state = 5U;
                } else {
                    __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state = 0xaU;
                }
            } else if ((((IData)(vlSelf->__PVT__normalizer__DOT__pool_selected) 
                         & (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__tbl_rsp_valid)) 
                        & (IData)(vlSelf->__PVT__normalizer__DOT__pool_tbl_ready))) {
                if (vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer_rsp_error) {
                    vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__failed = 1U;
                    vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__code = 4U;
                    __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state = 0xaU;
                } else {
                    vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__read_data 
                        = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer_rsp_data;
                    __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state = 9U;
                }
            }
        } else if ((4U & (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__state))) {
            if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__state))) {
                    if (((IData)(vlSelf->__PVT__normalizer__DOT__pool_tbl_valid) 
                         & ((IData)(vlSelf->__PVT__normalizer__DOT__pool_selected) 
                            & (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__tbl_req_ready)))) {
                        __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state = 8U;
                    }
                } else if ((IData)(((0U != vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__request_address[2U]) 
                                    | VL_GTE_W(3, vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__request_address, vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__table_end)))) {
                    vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__failed = 1U;
                    vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__code = 0x11U;
                    __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state = 0xaU;
                } else {
                    __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state = 7U;
                }
            } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__state))) {
                VL_ADD_W(3, __Vtemp_45, vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__data_start, vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value);
                vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__request_address[0U] 
                    = __Vtemp_45[0U];
                vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__request_address[1U] 
                    = __Vtemp_45[1U];
                vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__request_address[2U] 
                    = (3U & __Vtemp_45[2U]);
                __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state = 6U;
            } else if ((IData)(((((0ULL != (3ULL & vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__base)) 
                                  | (0U != vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__data_start[2U])) 
                                 | (0U != vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__table_end[2U])) 
                                | ((0U == vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__count) 
                                   | (vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__index 
                                      >= vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__count))))) {
                vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__failed = 1U;
                vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__code = 0x11U;
                __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state = 0xaU;
            } else {
                __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state = 5U;
            }
        } else if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__state))) {
            if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__state))) {
                __Vtemp_47[0U] = vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__count;
                __Vtemp_47[1U] = 0U;
                __Vtemp_47[2U] = 0U;
                VL_SHIFTL_WWI(66,66,32, __Vtemp_48, __Vtemp_47, 2U);
                VL_ADD_W(3, __Vtemp_49, vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__data_start, __Vtemp_48);
                vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__table_end[0U] 
                    = __Vtemp_49[0U];
                vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__table_end[1U] 
                    = __Vtemp_49[1U];
                vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__table_end[2U] 
                    = (3U & __Vtemp_49[2U]);
                __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state = 4U;
            } else {
                __Vtemp_51[0U] = 0x20U;
                __Vtemp_51[1U] = 0U;
                __Vtemp_51[2U] = 0U;
                __Vtemp_52[0U] = (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__base);
                __Vtemp_52[1U] = (IData)((vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__base 
                                          >> 0x20U));
                __Vtemp_52[2U] = 0U;
                VL_ADD_W(3, __Vtemp_53, __Vtemp_51, __Vtemp_52);
                vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__data_start[0U] 
                    = __Vtemp_53[0U];
                vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__data_start[1U] 
                    = __Vtemp_53[1U];
                vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__data_start[2U] 
                    = (3U & __Vtemp_53[2U]);
                __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state = 3U;
            }
        } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__state))) {
            __Vtemp_55[0U] = vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__index;
            __Vtemp_55[1U] = 0U;
            __Vtemp_55[2U] = 0U;
            VL_SHIFTL_WWI(66,66,32, __Vtemp_56, __Vtemp_55, 2U);
            __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value[0U] 
                = __Vtemp_56[0U];
            __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value[1U] 
                = __Vtemp_56[1U];
            __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value[2U] 
                = (3U & __Vtemp_56[2U]);
            __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state = 2U;
        } else if ((((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                     & (7U == (IData)(vlSelf->__PVT__normalizer__DOT__state))) 
                    & (IData)(vlSelf->__PVT__normalizer__DOT__pool_ready))) {
            vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__word_index = 0U;
            vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__base 
                = vlSelf->__PVT__normalizer__DOT__scalar_pool_base;
            vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__count 
                = vlSelf->__PVT__normalizer__DOT__scalar_pool_count;
            vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__index 
                = vlSelf->__PVT__normalizer__DOT__pool_cursor;
            vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__result_data = 0U;
            vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__failed = 0U;
            vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__code = 0U;
            __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state = 1U;
        }
    } else {
        __Vdly__normalizer__DOT__classification__DOT__state = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__admitted = 0U;
        __Vdly__normalizer__DOT__classification__DOT__failed = 0U;
        __Vdly__normalizer__DOT__classification__DOT__code = 0U;
        __Vdly__normalizer__DOT__classification__DOT__base = 0ULL;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__scalar = 0U;
        __Vdly__normalizer__DOT__classification__DOT__range_count = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__class_count = 0U;
        __Vdly__normalizer__DOT__classification__DOT__low_index = 0U;
        __Vdly__normalizer__DOT__classification__DOT__high_index = 0U;
        __Vdly__normalizer__DOT__classification__DOT__middle = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__first_scalar = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__last_scalar = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__class_value = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__property_value = 0U;
        vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__dividend_shift = 0U;
        __Vdly__normalizer__DOT__hangul_divider__DOT__divider__DOT__quotient_work = 0U;
        vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__iterations = 0U;
        __Vdly__normalizer__DOT__hangul_divider__DOT__divider__DOT__state = 0U;
        vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__divisor = 0U;
        vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__remainder_work = 0ULL;
        vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__quotient_result = 0U;
        vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__remainder_result = 0U;
        vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__zero_divisor = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__word_index = 0U;
        __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[0U] = 0U;
        __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[1U] = 0U;
        __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[2U] = 0U;
        __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__base = 0ULL;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__count = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__index = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__data_start[0U] = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__data_start[1U] = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__data_start[2U] = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__table_end[0U] = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__table_end[1U] = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__table_end[2U] = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__request_address[0U] = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__request_address[1U] = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__request_address[2U] = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[0U] = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[1U] = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[2U] = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[3U] = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__read_data = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__failed = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__code = 0U;
        __Vdly__normalizer__DOT__pool_cursor = 0U;
        vlSelf->__PVT__normalizer__DOT__pool_remaining = 0U;
        __Vdly__normalizer__DOT__hangul_product = 0U;
        __Vdly__normalizer__DOT__read_index = 0U;
        __Vdly__normalizer__DOT__write_index = 0U;
        __Vdly__normalizer__DOT__state = 0U;
        __Vdly__normalizer__DOT__mode = 0U;
        __Vdly__normalizer__DOT__scalar_count = 0U;
        vlSelf->__PVT__normalizer__DOT__input_scalar = 0U;
        __Vdly__normalizer__DOT__append_scalar = 0U;
        __Vdly__normalizer__DOT__insert_position = 0U;
        vlSelf->__PVT__normalizer__DOT__input_last = 0U;
        __Vdly__normalizer__DOT__append_source = 0U;
        __Vdly__normalizer__DOT__hangul_part = 0U;
        vlSelf->__PVT__normalizer__DOT__append_ccc = 0U;
        vlSelf->__PVT__normalizer__DOT__previous_ccc = 0U;
        vlSelf->__PVT__normalizer__DOT__previous_scalar = 0U;
        vlSelf->__PVT__normalizer__DOT__ranges_base = 0ULL;
        __Vdly__normalizer__DOT__decomposition_base = 0ULL;
        __Vdly__normalizer__DOT__scalar_pool_base = 0ULL;
        __Vdly__normalizer__DOT__composition_base = 0ULL;
        vlSelf->__PVT__normalizer__DOT__range_count = 0U;
        vlSelf->__PVT__normalizer__DOT__class_count = 0U;
        __Vdly__normalizer__DOT__decomposition_count = 0U;
        __Vdly__normalizer__DOT__scalar_pool_count = 0U;
        __Vdly__normalizer__DOT__composition_count = 0U;
        __Vdly__normalizer__DOT__search_low = 0U;
        __Vdly__normalizer__DOT__search_high = 0U;
        __Vdly__normalizer__DOT__search_middle = 0U;
        __Vdly__normalizer__DOT__reading_composition = 0U;
        vlSelf->__PVT__normalizer__DOT__record_value[0U] = 0U;
        vlSelf->__PVT__normalizer__DOT__record_value[1U] = 0U;
        vlSelf->__PVT__normalizer__DOT__record_value[2U] = 0U;
        vlSelf->__PVT__normalizer__DOT__record_value[3U] = 0U;
        vlSelf->__PVT__normalizer__DOT__hangul_index = 0U;
        vlSelf->__PVT__normalizer__DOT__hangul_l = 0U;
        __Vdly__normalizer__DOT__hangul_v = 0U;
        __Vdly__normalizer__DOT__hangul_t = 0U;
        vlSelf->__PVT__normalizer__DOT__hangul_l_index = 0U;
        vlSelf->__PVT__normalizer__DOT__hangul_v_index = 0U;
        __Vdly__normalizer__DOT__output_index = 0U;
        vlSelf->__PVT__normalizer__DOT__current_scalar = 0U;
        __Vdly__normalizer__DOT__starter_scalar = 0U;
        vlSelf->__PVT__normalizer__DOT__starter_position = 0U;
        __Vdly__normalizer__DOT__composite_scalar = 0U;
        vlSelf->__PVT__normalizer__DOT__current_ccc = 0U;
        __Vdly__normalizer__DOT__last_ccc = 0U;
        __Vdly__normalizer__DOT__starter_valid = 0U;
        vlSelf->__PVT__normalizer__DOT__code = 0U;
        vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__word_index = 0U;
        __Vdly__normalizer__DOT__records__DOT__reader__DOT__offset_value[0U] = 0U;
        __Vdly__normalizer__DOT__records__DOT__reader__DOT__offset_value[1U] = 0U;
        __Vdly__normalizer__DOT__records__DOT__reader__DOT__offset_value[2U] = 0U;
        __Vdly__normalizer__DOT__records__DOT__reader__DOT__state = 0U;
        vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__base = 0ULL;
        vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__count = 0U;
        vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__index = 0U;
        vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__data_start[0U] = 0U;
        vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__data_start[1U] = 0U;
        vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__data_start[2U] = 0U;
        vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__table_end[0U] = 0U;
        vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__table_end[1U] = 0U;
        vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__table_end[2U] = 0U;
        vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__request_address[0U] = 0U;
        vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__request_address[1U] = 0U;
        vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__request_address[2U] = 0U;
        vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__result_data[0U] = 0U;
        vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__result_data[1U] = 0U;
        vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__result_data[2U] = 0U;
        vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__result_data[3U] = 0U;
        vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__read_data = 0U;
        vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__failed = 0U;
        vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__code = 0U;
        vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__word_index = 0U;
        __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value[0U] = 0U;
        __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value[1U] = 0U;
        __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value[2U] = 0U;
        __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state = 0U;
        vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__base = 0ULL;
        vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__count = 0U;
        vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__index = 0U;
        vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__data_start[0U] = 0U;
        vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__data_start[1U] = 0U;
        vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__data_start[2U] = 0U;
        vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__table_end[0U] = 0U;
        vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__table_end[1U] = 0U;
        vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__table_end[2U] = 0U;
        vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__request_address[0U] = 0U;
        vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__request_address[1U] = 0U;
        vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__request_address[2U] = 0U;
        vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__result_data = 0U;
        vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__read_data = 0U;
        vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__failed = 0U;
        vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__code = 0U;
    }
    vlSelf->__PVT__normalizer__DOT__classification__DOT__high_index 
        = __Vdly__normalizer__DOT__classification__DOT__high_index;
    vlSelf->__PVT__normalizer__DOT__classification__DOT__low_index 
        = __Vdly__normalizer__DOT__classification__DOT__low_index;
    vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__quotient_work 
        = __Vdly__normalizer__DOT__hangul_divider__DOT__divider__DOT__quotient_work;
    vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__state 
        = __Vdly__normalizer__DOT__hangul_divider__DOT__divider__DOT__state;
    vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__shifted_remainder 
        = (0x1ffffffffULL & (VL_SHIFTL_QQI(33,33,32, vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__remainder_work, 1U) 
                             | (QData)((IData)((vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__dividend_shift 
                                                >> 0x1fU)))));
    vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[0U] 
        = __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[0U];
    vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[1U] 
        = __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[1U];
    vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[2U] 
        = __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[2U];
    vlSelf->__PVT__normalizer__DOT__classification__DOT__base 
        = __Vdly__normalizer__DOT__classification__DOT__base;
    vlSelf->__PVT__normalizer__DOT__classification__DOT__range_count 
        = __Vdly__normalizer__DOT__classification__DOT__range_count;
    vlSelf->__PVT__normalizer__DOT__classification__DOT__middle 
        = __Vdly__normalizer__DOT__classification__DOT__middle;
    vlSelf->__PVT__normalizer__DOT__classification__DOT__state 
        = __Vdly__normalizer__DOT__classification__DOT__state;
    vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state 
        = __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state;
    vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__subtract 
        = (vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__shifted_remainder 
           >= (QData)((IData)(vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__divisor)));
    vlSelf->__PVT__normalizer__DOT__classification__DOT__code 
        = __Vdly__normalizer__DOT__classification__DOT__code;
    vlSelf->__PVT__normalizer__DOT__mode = __Vdly__normalizer__DOT__mode;
    vlSelf->__PVT__normalizer__DOT__composite_scalar 
        = __Vdly__normalizer__DOT__composite_scalar;
    vlSelf->__PVT__normalizer__DOT__hangul_product 
        = __Vdly__normalizer__DOT__hangul_product;
    vlSelf->__PVT__normalizer__DOT__read_index = __Vdly__normalizer__DOT__read_index;
    vlSelf->__PVT__normalizer__DOT__last_ccc = __Vdly__normalizer__DOT__last_ccc;
    vlSelf->__PVT__normalizer__DOT__starter_valid = __Vdly__normalizer__DOT__starter_valid;
    vlSelf->__PVT__normalizer__DOT__write_index = __Vdly__normalizer__DOT__write_index;
    vlSelf->__PVT__normalizer__DOT__search_low = __Vdly__normalizer__DOT__search_low;
    vlSelf->__PVT__normalizer__DOT__search_high = __Vdly__normalizer__DOT__search_high;
    vlSelf->__PVT__normalizer__DOT__hangul_v = __Vdly__normalizer__DOT__hangul_v;
    vlSelf->__PVT__normalizer__DOT__hangul_t = __Vdly__normalizer__DOT__hangul_t;
    vlSelf->__PVT__normalizer__DOT__append_source = __Vdly__normalizer__DOT__append_source;
    vlSelf->__PVT__normalizer__DOT__hangul_part = __Vdly__normalizer__DOT__hangul_part;
    vlSelf->__PVT__normalizer__DOT__append_scalar = __Vdly__normalizer__DOT__append_scalar;
    vlSelf->__PVT__normalizer__DOT__insert_position 
        = __Vdly__normalizer__DOT__insert_position;
    vlSelf->__PVT__normalizer__DOT__classification__DOT__failed 
        = __Vdly__normalizer__DOT__classification__DOT__failed;
    vlSelf->__PVT__normalizer__DOT__scalar_count = __Vdly__normalizer__DOT__scalar_count;
    vlSelf->__PVT__normalizer__DOT__output_index = __Vdly__normalizer__DOT__output_index;
    vlSelf->__PVT__normalizer__DOT__starter_scalar 
        = __Vdly__normalizer__DOT__starter_scalar;
    if (__Vdlyvset__normalizer__DOT__combining_classes__v0) {
        vlSelf->__PVT__normalizer__DOT__combining_classes[__Vdlyvdim0__normalizer__DOT__combining_classes__v0] 
            = __Vdlyvval__normalizer__DOT__combining_classes__v0;
    }
    if (__Vdlyvset__normalizer__DOT__scalars__v2) {
        vlSelf->__PVT__normalizer__DOT__combining_classes[__Vdlyvdim0__normalizer__DOT__combining_classes__v1] 
            = __Vdlyvval__normalizer__DOT__combining_classes__v1;
    }
    if (__Vdlyvset__normalizer__DOT__scalars__v0) {
        vlSelf->__PVT__normalizer__DOT__scalars[__Vdlyvdim0__normalizer__DOT__scalars__v0] 
            = __Vdlyvval__normalizer__DOT__scalars__v0;
    }
    if (__Vdlyvset__normalizer__DOT__scalars__v1) {
        vlSelf->__PVT__normalizer__DOT__scalars[__Vdlyvdim0__normalizer__DOT__scalars__v1] 
            = __Vdlyvval__normalizer__DOT__scalars__v1;
    }
    if (__Vdlyvset__normalizer__DOT__scalars__v2) {
        vlSelf->__PVT__normalizer__DOT__scalars[__Vdlyvdim0__normalizer__DOT__scalars__v2] 
            = __Vdlyvval__normalizer__DOT__scalars__v2;
    }
    if (__Vdlyvset__normalizer__DOT__scalars__v3) {
        vlSelf->__PVT__normalizer__DOT__combining_classes[__Vdlyvdim0__normalizer__DOT__combining_classes__v2] 
            = __Vdlyvval__normalizer__DOT__combining_classes__v2;
        vlSelf->__PVT__normalizer__DOT__scalars[__Vdlyvdim0__normalizer__DOT__scalars__v3] 
            = __Vdlyvval__normalizer__DOT__scalars__v3;
    }
    vlSelf->__PVT__normalizer__DOT__record_scalar_valid 
        = ((~ ((0xd800U <= vlSelf->__PVT__normalizer__DOT__record_value[0U]) 
               & (0xdfffU >= vlSelf->__PVT__normalizer__DOT__record_value[0U]))) 
           & (0x10ffffU >= vlSelf->__PVT__normalizer__DOT__record_value[0U]));
    vlSelf->__PVT__normalizer__DOT__pool_end = (0x1ffffffffULL 
                                                & ((QData)((IData)(
                                                                   vlSelf->__PVT__normalizer__DOT__record_value[1U])) 
                                                   + (QData)((IData)(
                                                                     vlSelf->__PVT__normalizer__DOT__record_value[2U]))));
    __VdfgTmp_hd39cf095__0 = (vlSelf->__PVT__normalizer__DOT__record_value[0U] 
                              == vlSelf->__PVT__normalizer__DOT__starter_scalar);
    vlSelf->__PVT__normalizer__DOT__composition_equal 
        = ((IData)(__VdfgTmp_hd39cf095__0) & (vlSelf->__PVT__normalizer__DOT__record_value[1U] 
                                              == vlSelf->__PVT__normalizer__DOT__current_scalar));
    vlSelf->__PVT__normalizer__DOT__composition_before 
        = ((vlSelf->__PVT__normalizer__DOT__record_value[0U] 
            < vlSelf->__PVT__normalizer__DOT__starter_scalar) 
           | ((IData)(__VdfgTmp_hd39cf095__0) & (vlSelf->__PVT__normalizer__DOT__record_value[1U] 
                                                 < vlSelf->__PVT__normalizer__DOT__current_scalar)));
    vlSelf->__PVT__normalizer__DOT__composition_base 
        = __Vdly__normalizer__DOT__composition_base;
    vlSelf->__PVT__normalizer__DOT__decomposition_base 
        = __Vdly__normalizer__DOT__decomposition_base;
    vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__offset_value[0U] 
        = __Vdly__normalizer__DOT__records__DOT__reader__DOT__offset_value[0U];
    vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__offset_value[1U] 
        = __Vdly__normalizer__DOT__records__DOT__reader__DOT__offset_value[1U];
    vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__offset_value[2U] 
        = __Vdly__normalizer__DOT__records__DOT__reader__DOT__offset_value[2U];
    vlSelf->__PVT__normalizer__DOT__reading_composition 
        = __Vdly__normalizer__DOT__reading_composition;
    vlSelf->__PVT__normalizer__DOT__composition_count 
        = __Vdly__normalizer__DOT__composition_count;
    vlSelf->__PVT__normalizer__DOT__decomposition_count 
        = __Vdly__normalizer__DOT__decomposition_count;
    vlSelf->__PVT__normalizer__DOT__search_middle = __Vdly__normalizer__DOT__search_middle;
    vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__state 
        = __Vdly__normalizer__DOT__records__DOT__reader__DOT__state;
    vlSelf->__PVT__normalizer__DOT__scalar_pool_base 
        = __Vdly__normalizer__DOT__scalar_pool_base;
    vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value[0U] 
        = __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value[0U];
    vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value[1U] 
        = __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value[1U];
    vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value[2U] 
        = __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value[2U];
    vlSelf->__PVT__normalizer__DOT__scalar_pool_count 
        = __Vdly__normalizer__DOT__scalar_pool_count;
    vlSelf->__PVT__normalizer__DOT__pool_cursor = __Vdly__normalizer__DOT__pool_cursor;
    vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__state 
        = __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state;
    vlSelf->__PVT__normalizer__DOT__state = __Vdly__normalizer__DOT__state;
    vlSelf->__PVT__normalizer__DOT__classify_selected 
        = ((0xaU == (IData)(vlSelf->__PVT__normalizer__DOT__state)) 
           | (0xbU == (IData)(vlSelf->__PVT__normalizer__DOT__state)));
    vlSelf->__PVT__normalizer__DOT__pool_selected = 
        ((7U == (IData)(vlSelf->__PVT__normalizer__DOT__state)) 
         | (8U == (IData)(vlSelf->__PVT__normalizer__DOT__state)));
    vlSelf->__VdfgTmp_h0a1e14da__0 = (1U & ((~ (IData)(vlSelf->__PVT__normalizer__DOT__classify_selected)) 
                                            & (~ (IData)(vlSelf->__PVT__normalizer__DOT__pool_selected))));
}

VL_INLINE_OPT void Vbench_anvil_edge_normalizer__M10___act_comb__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__normalization__0(Vbench_anvil_edge_normalizer__M10* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+              Vbench_anvil_edge_normalizer__M10___act_comb__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__normalization__0\n"); );
    // Body
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

VL_INLINE_OPT void Vbench_anvil_edge_normalizer__M10___nba_sequent__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__normalization__0(Vbench_anvil_edge_normalizer__M10* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+              Vbench_anvil_edge_normalizer__M10___nba_sequent__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__normalization__0\n"); );
    // Init
    CData/*0:0*/ __VdfgTmp_hd39cf095__0;
    __VdfgTmp_hd39cf095__0 = 0;
    CData/*5:0*/ __Vdly__normalizer__DOT__state;
    __Vdly__normalizer__DOT__state = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__mode;
    __Vdly__normalizer__DOT__mode = 0;
    QData/*63:0*/ __Vdly__normalizer__DOT__decomposition_base;
    __Vdly__normalizer__DOT__decomposition_base = 0;
    QData/*63:0*/ __Vdly__normalizer__DOT__scalar_pool_base;
    __Vdly__normalizer__DOT__scalar_pool_base = 0;
    QData/*63:0*/ __Vdly__normalizer__DOT__composition_base;
    __Vdly__normalizer__DOT__composition_base = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__decomposition_count;
    __Vdly__normalizer__DOT__decomposition_count = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__scalar_pool_count;
    __Vdly__normalizer__DOT__scalar_pool_count = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__composition_count;
    __Vdly__normalizer__DOT__composition_count = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__scalar_count;
    __Vdly__normalizer__DOT__scalar_count = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__output_index;
    __Vdly__normalizer__DOT__output_index = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__composite_scalar;
    __Vdly__normalizer__DOT__composite_scalar = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__hangul_product;
    __Vdly__normalizer__DOT__hangul_product = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__read_index;
    __Vdly__normalizer__DOT__read_index = 0;
    CData/*3:0*/ __Vdlyvdim0__normalizer__DOT__scalars__v0;
    __Vdlyvdim0__normalizer__DOT__scalars__v0 = 0;
    IData/*31:0*/ __Vdlyvval__normalizer__DOT__scalars__v0;
    __Vdlyvval__normalizer__DOT__scalars__v0 = 0;
    CData/*0:0*/ __Vdlyvset__normalizer__DOT__scalars__v0;
    __Vdlyvset__normalizer__DOT__scalars__v0 = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__starter_scalar;
    __Vdly__normalizer__DOT__starter_scalar = 0;
    CData/*3:0*/ __Vdlyvdim0__normalizer__DOT__scalars__v1;
    __Vdlyvdim0__normalizer__DOT__scalars__v1 = 0;
    IData/*31:0*/ __Vdlyvval__normalizer__DOT__scalars__v1;
    __Vdlyvval__normalizer__DOT__scalars__v1 = 0;
    CData/*0:0*/ __Vdlyvset__normalizer__DOT__scalars__v1;
    __Vdlyvset__normalizer__DOT__scalars__v1 = 0;
    CData/*7:0*/ __Vdly__normalizer__DOT__last_ccc;
    __Vdly__normalizer__DOT__last_ccc = 0;
    CData/*3:0*/ __Vdlyvdim0__normalizer__DOT__combining_classes__v0;
    __Vdlyvdim0__normalizer__DOT__combining_classes__v0 = 0;
    CData/*7:0*/ __Vdlyvval__normalizer__DOT__combining_classes__v0;
    __Vdlyvval__normalizer__DOT__combining_classes__v0 = 0;
    CData/*0:0*/ __Vdlyvset__normalizer__DOT__combining_classes__v0;
    __Vdlyvset__normalizer__DOT__combining_classes__v0 = 0;
    CData/*0:0*/ __Vdly__normalizer__DOT__starter_valid;
    __Vdly__normalizer__DOT__starter_valid = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__write_index;
    __Vdly__normalizer__DOT__write_index = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__search_low;
    __Vdly__normalizer__DOT__search_low = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__search_high;
    __Vdly__normalizer__DOT__search_high = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__search_middle;
    __Vdly__normalizer__DOT__search_middle = 0;
    CData/*0:0*/ __Vdly__normalizer__DOT__reading_composition;
    __Vdly__normalizer__DOT__reading_composition = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__hangul_v;
    __Vdly__normalizer__DOT__hangul_v = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__hangul_t;
    __Vdly__normalizer__DOT__hangul_t = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__append_scalar;
    __Vdly__normalizer__DOT__append_scalar = 0;
    CData/*1:0*/ __Vdly__normalizer__DOT__append_source;
    __Vdly__normalizer__DOT__append_source = 0;
    CData/*1:0*/ __Vdly__normalizer__DOT__hangul_part;
    __Vdly__normalizer__DOT__hangul_part = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__pool_cursor;
    __Vdly__normalizer__DOT__pool_cursor = 0;
    CData/*3:0*/ __Vdlyvdim0__normalizer__DOT__scalars__v2;
    __Vdlyvdim0__normalizer__DOT__scalars__v2 = 0;
    IData/*31:0*/ __Vdlyvval__normalizer__DOT__scalars__v2;
    __Vdlyvval__normalizer__DOT__scalars__v2 = 0;
    CData/*0:0*/ __Vdlyvset__normalizer__DOT__scalars__v2;
    __Vdlyvset__normalizer__DOT__scalars__v2 = 0;
    CData/*3:0*/ __Vdlyvdim0__normalizer__DOT__combining_classes__v1;
    __Vdlyvdim0__normalizer__DOT__combining_classes__v1 = 0;
    CData/*7:0*/ __Vdlyvval__normalizer__DOT__combining_classes__v1;
    __Vdlyvval__normalizer__DOT__combining_classes__v1 = 0;
    CData/*3:0*/ __Vdlyvdim0__normalizer__DOT__scalars__v3;
    __Vdlyvdim0__normalizer__DOT__scalars__v3 = 0;
    IData/*31:0*/ __Vdlyvval__normalizer__DOT__scalars__v3;
    __Vdlyvval__normalizer__DOT__scalars__v3 = 0;
    CData/*0:0*/ __Vdlyvset__normalizer__DOT__scalars__v3;
    __Vdlyvset__normalizer__DOT__scalars__v3 = 0;
    CData/*3:0*/ __Vdlyvdim0__normalizer__DOT__combining_classes__v2;
    __Vdlyvdim0__normalizer__DOT__combining_classes__v2 = 0;
    CData/*7:0*/ __Vdlyvval__normalizer__DOT__combining_classes__v2;
    __Vdlyvval__normalizer__DOT__combining_classes__v2 = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__insert_position;
    __Vdly__normalizer__DOT__insert_position = 0;
    CData/*3:0*/ __Vdly__normalizer__DOT__records__DOT__reader__DOT__state;
    __Vdly__normalizer__DOT__records__DOT__reader__DOT__state = 0;
    VlWide<3>/*65:0*/ __Vdly__normalizer__DOT__records__DOT__reader__DOT__offset_value;
    VL_ZERO_W(66, __Vdly__normalizer__DOT__records__DOT__reader__DOT__offset_value);
    CData/*3:0*/ __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state;
    __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state = 0;
    VlWide<3>/*65:0*/ __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value;
    VL_ZERO_W(66, __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value);
    CData/*0:0*/ __Vdly__normalizer__DOT__classification__DOT__failed;
    __Vdly__normalizer__DOT__classification__DOT__failed = 0;
    CData/*7:0*/ __Vdly__normalizer__DOT__classification__DOT__code;
    __Vdly__normalizer__DOT__classification__DOT__code = 0;
    CData/*3:0*/ __Vdly__normalizer__DOT__classification__DOT__state;
    __Vdly__normalizer__DOT__classification__DOT__state = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__classification__DOT__high_index;
    __Vdly__normalizer__DOT__classification__DOT__high_index = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__classification__DOT__low_index;
    __Vdly__normalizer__DOT__classification__DOT__low_index = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__classification__DOT__middle;
    __Vdly__normalizer__DOT__classification__DOT__middle = 0;
    QData/*63:0*/ __Vdly__normalizer__DOT__classification__DOT__base;
    __Vdly__normalizer__DOT__classification__DOT__base = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__classification__DOT__range_count;
    __Vdly__normalizer__DOT__classification__DOT__range_count = 0;
    CData/*3:0*/ __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state;
    __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 0;
    VlWide<3>/*65:0*/ __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value;
    VL_ZERO_W(66, __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value);
    CData/*1:0*/ __Vdly__normalizer__DOT__hangul_divider__DOT__divider__DOT__state;
    __Vdly__normalizer__DOT__hangul_divider__DOT__divider__DOT__state = 0;
    IData/*31:0*/ __Vdly__normalizer__DOT__hangul_divider__DOT__divider__DOT__quotient_work;
    __Vdly__normalizer__DOT__hangul_divider__DOT__divider__DOT__quotient_work = 0;
    VlWide<3>/*95:0*/ __Vtemp_5;
    VlWide<3>/*95:0*/ __Vtemp_6;
    VlWide<3>/*95:0*/ __Vtemp_8;
    VlWide<3>/*95:0*/ __Vtemp_10;
    VlWide<3>/*95:0*/ __Vtemp_11;
    VlWide<3>/*95:0*/ __Vtemp_12;
    VlWide<3>/*95:0*/ __Vtemp_14;
    VlWide<3>/*95:0*/ __Vtemp_15;
    VlWide<3>/*95:0*/ __Vtemp_16;
    VlWide<3>/*95:0*/ __Vtemp_18;
    VlWide<3>/*95:0*/ __Vtemp_19;
    VlWide<3>/*95:0*/ __Vtemp_25;
    VlWide<3>/*95:0*/ __Vtemp_26;
    VlWide<3>/*95:0*/ __Vtemp_28;
    VlWide<3>/*95:0*/ __Vtemp_30;
    VlWide<3>/*95:0*/ __Vtemp_31;
    VlWide<3>/*95:0*/ __Vtemp_32;
    VlWide<3>/*95:0*/ __Vtemp_34;
    VlWide<3>/*95:0*/ __Vtemp_35;
    VlWide<3>/*95:0*/ __Vtemp_36;
    VlWide<3>/*95:0*/ __Vtemp_38;
    VlWide<3>/*95:0*/ __Vtemp_39;
    VlWide<3>/*95:0*/ __Vtemp_42;
    VlWide<3>/*95:0*/ __Vtemp_43;
    VlWide<3>/*95:0*/ __Vtemp_45;
    VlWide<3>/*95:0*/ __Vtemp_47;
    VlWide<3>/*95:0*/ __Vtemp_48;
    VlWide<3>/*95:0*/ __Vtemp_49;
    VlWide<3>/*95:0*/ __Vtemp_51;
    VlWide<3>/*95:0*/ __Vtemp_52;
    VlWide<3>/*95:0*/ __Vtemp_53;
    VlWide<3>/*95:0*/ __Vtemp_55;
    VlWide<3>/*95:0*/ __Vtemp_56;
    // Body
    __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[0U] 
        = vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[0U];
    __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[1U] 
        = vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[1U];
    __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[2U] 
        = vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[2U];
    __Vdly__normalizer__DOT__records__DOT__reader__DOT__offset_value[0U] 
        = vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__offset_value[0U];
    __Vdly__normalizer__DOT__records__DOT__reader__DOT__offset_value[1U] 
        = vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__offset_value[1U];
    __Vdly__normalizer__DOT__records__DOT__reader__DOT__offset_value[2U] 
        = vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__offset_value[2U];
    __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state 
        = vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state;
    __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value[0U] 
        = vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value[0U];
    __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value[1U] 
        = vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value[1U];
    __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value[2U] 
        = vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value[2U];
    __Vdly__normalizer__DOT__records__DOT__reader__DOT__state 
        = vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__state;
    __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state 
        = vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__state;
    __Vdly__normalizer__DOT__insert_position = vlSelf->__PVT__normalizer__DOT__insert_position;
    __Vdly__normalizer__DOT__pool_cursor = vlSelf->__PVT__normalizer__DOT__pool_cursor;
    __Vdly__normalizer__DOT__hangul_part = vlSelf->__PVT__normalizer__DOT__hangul_part;
    __Vdly__normalizer__DOT__append_source = vlSelf->__PVT__normalizer__DOT__append_source;
    __Vdly__normalizer__DOT__append_scalar = vlSelf->__PVT__normalizer__DOT__append_scalar;
    __Vdly__normalizer__DOT__hangul_t = vlSelf->__PVT__normalizer__DOT__hangul_t;
    __Vdly__normalizer__DOT__hangul_v = vlSelf->__PVT__normalizer__DOT__hangul_v;
    __Vdly__normalizer__DOT__reading_composition = vlSelf->__PVT__normalizer__DOT__reading_composition;
    __Vdly__normalizer__DOT__search_middle = vlSelf->__PVT__normalizer__DOT__search_middle;
    __Vdly__normalizer__DOT__search_high = vlSelf->__PVT__normalizer__DOT__search_high;
    __Vdly__normalizer__DOT__search_low = vlSelf->__PVT__normalizer__DOT__search_low;
    __Vdly__normalizer__DOT__write_index = vlSelf->__PVT__normalizer__DOT__write_index;
    __Vdly__normalizer__DOT__starter_valid = vlSelf->__PVT__normalizer__DOT__starter_valid;
    __Vdly__normalizer__DOT__last_ccc = vlSelf->__PVT__normalizer__DOT__last_ccc;
    __Vdly__normalizer__DOT__read_index = vlSelf->__PVT__normalizer__DOT__read_index;
    __Vdly__normalizer__DOT__hangul_product = vlSelf->__PVT__normalizer__DOT__hangul_product;
    __Vdly__normalizer__DOT__composite_scalar = vlSelf->__PVT__normalizer__DOT__composite_scalar;
    __Vdly__normalizer__DOT__composition_count = vlSelf->__PVT__normalizer__DOT__composition_count;
    __Vdly__normalizer__DOT__scalar_pool_count = vlSelf->__PVT__normalizer__DOT__scalar_pool_count;
    __Vdly__normalizer__DOT__decomposition_count = vlSelf->__PVT__normalizer__DOT__decomposition_count;
    __Vdly__normalizer__DOT__composition_base = vlSelf->__PVT__normalizer__DOT__composition_base;
    __Vdly__normalizer__DOT__scalar_pool_base = vlSelf->__PVT__normalizer__DOT__scalar_pool_base;
    __Vdly__normalizer__DOT__decomposition_base = vlSelf->__PVT__normalizer__DOT__decomposition_base;
    __Vdly__normalizer__DOT__mode = vlSelf->__PVT__normalizer__DOT__mode;
    __Vdly__normalizer__DOT__output_index = vlSelf->__PVT__normalizer__DOT__output_index;
    __Vdly__normalizer__DOT__scalar_count = vlSelf->__PVT__normalizer__DOT__scalar_count;
    __Vdlyvset__normalizer__DOT__combining_classes__v0 = 0U;
    __Vdlyvset__normalizer__DOT__scalars__v0 = 0U;
    __Vdlyvset__normalizer__DOT__scalars__v1 = 0U;
    __Vdly__normalizer__DOT__starter_scalar = vlSelf->__PVT__normalizer__DOT__starter_scalar;
    __Vdlyvset__normalizer__DOT__scalars__v2 = 0U;
    __Vdlyvset__normalizer__DOT__scalars__v3 = 0U;
    __Vdly__normalizer__DOT__state = vlSelf->__PVT__normalizer__DOT__state;
    __Vdly__normalizer__DOT__hangul_divider__DOT__divider__DOT__quotient_work 
        = vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__quotient_work;
    __Vdly__normalizer__DOT__hangul_divider__DOT__divider__DOT__state 
        = vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__state;
    __Vdly__normalizer__DOT__classification__DOT__range_count 
        = vlSelf->__PVT__normalizer__DOT__classification__DOT__range_count;
    __Vdly__normalizer__DOT__classification__DOT__base 
        = vlSelf->__PVT__normalizer__DOT__classification__DOT__base;
    __Vdly__normalizer__DOT__classification__DOT__middle 
        = vlSelf->__PVT__normalizer__DOT__classification__DOT__middle;
    __Vdly__normalizer__DOT__classification__DOT__low_index 
        = vlSelf->__PVT__normalizer__DOT__classification__DOT__low_index;
    __Vdly__normalizer__DOT__classification__DOT__high_index 
        = vlSelf->__PVT__normalizer__DOT__classification__DOT__high_index;
    __Vdly__normalizer__DOT__classification__DOT__code 
        = vlSelf->__PVT__normalizer__DOT__classification__DOT__code;
    __Vdly__normalizer__DOT__classification__DOT__failed 
        = vlSelf->__PVT__normalizer__DOT__classification__DOT__failed;
    __Vdly__normalizer__DOT__classification__DOT__state 
        = vlSelf->__PVT__normalizer__DOT__classification__DOT__state;
    if (vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) {
        if ((8U & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__state))) {
            __Vdly__normalizer__DOT__classification__DOT__failed = 1U;
            __Vdly__normalizer__DOT__classification__DOT__code = 0x12U;
            __Vdly__normalizer__DOT__classification__DOT__state = 6U;
        } else if ((4U & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__state))) {
            if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__state))) {
                    __Vdly__normalizer__DOT__classification__DOT__failed = 1U;
                    __Vdly__normalizer__DOT__classification__DOT__code = 0x12U;
                    __Vdly__normalizer__DOT__classification__DOT__state = 6U;
                } else if (((IData)(vlSelf->__PVT__normalizer__DOT__class_valid) 
                            & ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                               & (0xbU == (IData)(vlSelf->__PVT__normalizer__DOT__state))))) {
                    __Vdly__normalizer__DOT__classification__DOT__state = 0U;
                }
            } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__state))) {
                if ((((((vlSelf->__PVT__normalizer__DOT__classification__DOT__first_scalar 
                         > vlSelf->__PVT__normalizer__DOT__classification__DOT__last_scalar) 
                        | (0x10ffffU < vlSelf->__PVT__normalizer__DOT__classification__DOT__last_scalar)) 
                       | ((0xdfffU >= vlSelf->__PVT__normalizer__DOT__classification__DOT__first_scalar) 
                          & (0xd800U <= vlSelf->__PVT__normalizer__DOT__classification__DOT__last_scalar))) 
                      | (vlSelf->__PVT__normalizer__DOT__classification__DOT__class_value 
                         >= vlSelf->__PVT__normalizer__DOT__classification__DOT__class_count)) 
                     | (0U != (vlSelf->__PVT__normalizer__DOT__classification__DOT__property_value 
                               >> 0xaU)))) {
                    __Vdly__normalizer__DOT__classification__DOT__failed = 1U;
                    __Vdly__normalizer__DOT__classification__DOT__code = 0x12U;
                    __Vdly__normalizer__DOT__classification__DOT__state = 6U;
                } else if ((vlSelf->__PVT__normalizer__DOT__classification__DOT__scalar 
                            < vlSelf->__PVT__normalizer__DOT__classification__DOT__first_scalar)) {
                    __Vdly__normalizer__DOT__classification__DOT__high_index 
                        = vlSelf->__PVT__normalizer__DOT__classification__DOT__middle;
                    __Vdly__normalizer__DOT__classification__DOT__state = 2U;
                } else if ((vlSelf->__PVT__normalizer__DOT__classification__DOT__scalar 
                            > vlSelf->__PVT__normalizer__DOT__classification__DOT__last_scalar)) {
                    __Vdly__normalizer__DOT__classification__DOT__low_index 
                        = ((IData)(1U) + vlSelf->__PVT__normalizer__DOT__classification__DOT__middle);
                    __Vdly__normalizer__DOT__classification__DOT__state = 2U;
                } else {
                    __Vdly__normalizer__DOT__classification__DOT__state = 6U;
                }
            } else if (vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_valid) {
                if (((IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_valid) 
                     & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__failed))) {
                    __Vdly__normalizer__DOT__classification__DOT__failed = 1U;
                    __Vdly__normalizer__DOT__classification__DOT__code 
                        = ((IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_valid)
                            ? (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__code)
                            : 0U);
                    __Vdly__normalizer__DOT__classification__DOT__state = 6U;
                } else {
                    vlSelf->__PVT__normalizer__DOT__classification__DOT__first_scalar 
                        = vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_data[0U];
                    vlSelf->__PVT__normalizer__DOT__classification__DOT__last_scalar 
                        = vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_data[1U];
                    vlSelf->__PVT__normalizer__DOT__classification__DOT__class_value 
                        = vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_data[2U];
                    vlSelf->__PVT__normalizer__DOT__classification__DOT__property_value 
                        = vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_data[3U];
                    __Vdly__normalizer__DOT__classification__DOT__state = 5U;
                }
            }
        } else if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__state))) {
            if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__state))) {
                if (vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_ready) {
                    __Vdly__normalizer__DOT__classification__DOT__state = 4U;
                }
            } else if ((vlSelf->__PVT__normalizer__DOT__classification__DOT__low_index 
                        >= vlSelf->__PVT__normalizer__DOT__classification__DOT__high_index)) {
                __Vdly__normalizer__DOT__classification__DOT__failed = 1U;
                __Vdly__normalizer__DOT__classification__DOT__code = 0x12U;
                __Vdly__normalizer__DOT__classification__DOT__state = 6U;
            } else {
                __Vdly__normalizer__DOT__classification__DOT__middle 
                    = (vlSelf->__PVT__normalizer__DOT__classification__DOT__low_index 
                       + VL_SHIFTR_III(32,32,32, (vlSelf->__PVT__normalizer__DOT__classification__DOT__high_index 
                                                  - vlSelf->__PVT__normalizer__DOT__classification__DOT__low_index), 1U));
                __Vdly__normalizer__DOT__classification__DOT__state = 3U;
            }
        } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__state))) {
            if (((0x10ffffU < vlSelf->__PVT__normalizer__DOT__classification__DOT__scalar) 
                 | ((0xd800U <= vlSelf->__PVT__normalizer__DOT__classification__DOT__scalar) 
                    & (0xdfffU >= vlSelf->__PVT__normalizer__DOT__classification__DOT__scalar)))) {
                __Vdly__normalizer__DOT__classification__DOT__failed = 1U;
                __Vdly__normalizer__DOT__classification__DOT__code = 0x10U;
                __Vdly__normalizer__DOT__classification__DOT__state = 6U;
            } else if ((1U & ((((~ (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__admitted)) 
                                | (0U == vlSelf->__PVT__normalizer__DOT__classification__DOT__range_count)) 
                               | (0U == vlSelf->__PVT__normalizer__DOT__classification__DOT__class_count)) 
                              | (0U != (3U & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__base)))))) {
                __Vdly__normalizer__DOT__classification__DOT__failed = 1U;
                __Vdly__normalizer__DOT__classification__DOT__code = 6U;
                __Vdly__normalizer__DOT__classification__DOT__state = 6U;
            } else {
                __Vdly__normalizer__DOT__classification__DOT__state = 2U;
            }
        } else if ((((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                     & (0xaU == (IData)(vlSelf->__PVT__normalizer__DOT__state))) 
                    & (IData)(vlSelf->__PVT__normalizer__DOT__class_ready))) {
            vlSelf->__PVT__normalizer__DOT__classification__DOT__admitted = 1U;
            __Vdly__normalizer__DOT__classification__DOT__base 
                = vlSelf->__PVT__normalizer__DOT__ranges_base;
            __Vdly__normalizer__DOT__classification__DOT__range_count 
                = vlSelf->__PVT__normalizer__DOT__range_count;
            vlSelf->__PVT__normalizer__DOT__classification__DOT__class_count 
                = vlSelf->__PVT__normalizer__DOT__class_count;
            vlSelf->__PVT__normalizer__DOT__classification__DOT__scalar 
                = vlSelf->__PVT__normalizer__DOT__append_scalar;
            __Vdly__normalizer__DOT__classification__DOT__low_index = 0U;
            __Vdly__normalizer__DOT__classification__DOT__high_index 
                = vlSelf->__PVT__normalizer__DOT__range_count;
            __Vdly__normalizer__DOT__classification__DOT__failed = 0U;
            __Vdly__normalizer__DOT__classification__DOT__code = 0U;
            vlSelf->__PVT__normalizer__DOT__classification__DOT__class_value = 0U;
            vlSelf->__PVT__normalizer__DOT__classification__DOT__property_value = 0U;
            __Vdly__normalizer__DOT__classification__DOT__state = 1U;
        }
        if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__state))) {
            if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__state))) {
                if (((IData)(vlSelf->__PVT__normalizer__DOT__divider_valid) 
                     & ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                        & ((0x12U == (IData)(vlSelf->__PVT__normalizer__DOT__state)) 
                           | ((0x14U == (IData)(vlSelf->__PVT__normalizer__DOT__state)) 
                              | (0x23U == (IData)(vlSelf->__PVT__normalizer__DOT__state))))))) {
                    __Vdly__normalizer__DOT__hangul_divider__DOT__divider__DOT__state = 0U;
                }
            } else {
                if (vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__zero_divisor) {
                    vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__quotient_result = 0U;
                    vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__remainder_result = 0U;
                } else {
                    vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__quotient_result 
                        = vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__quotient_work;
                    vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__remainder_result 
                        = (IData)(vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__remainder_work);
                }
                __Vdly__normalizer__DOT__hangul_divider__DOT__divider__DOT__state = 3U;
            }
        } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__state))) {
            vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__dividend_shift 
                = VL_SHIFTL_III(32,32,32, vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__dividend_shift, 1U);
            if (vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__subtract) {
                __Vdly__normalizer__DOT__hangul_divider__DOT__divider__DOT__quotient_work 
                    = (1U | VL_SHIFTL_III(32,32,32, vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__quotient_work, 1U));
                vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__remainder_work 
                    = (0x1ffffffffULL & (vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__shifted_remainder 
                                         - (QData)((IData)(vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__divisor))));
            } else {
                __Vdly__normalizer__DOT__hangul_divider__DOT__divider__DOT__quotient_work 
                    = VL_SHIFTL_III(32,32,32, vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__quotient_work, 1U);
                vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__remainder_work 
                    = vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__shifted_remainder;
            }
            if ((0x1fU == (IData)(vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__iterations))) {
                __Vdly__normalizer__DOT__hangul_divider__DOT__divider__DOT__state = 2U;
            } else {
                vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__iterations 
                    = (0x3fU & ((IData)(1U) + (IData)(vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__iterations)));
            }
        } else if ((((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                     & ((0x11U == (IData)(vlSelf->__PVT__normalizer__DOT__state)) 
                        | ((0x13U == (IData)(vlSelf->__PVT__normalizer__DOT__state)) 
                           | (0x22U == (IData)(vlSelf->__PVT__normalizer__DOT__state))))) 
                    & (IData)(vlSelf->__PVT__normalizer__DOT__divider_ready))) {
            vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__dividend_shift 
                = ((0x22U == (IData)(vlSelf->__PVT__normalizer__DOT__state))
                    ? (vlSelf->__PVT__normalizer__DOT__starter_scalar 
                       - (IData)(0xac00U)) : vlSelf->__PVT__normalizer__DOT__hangul_index);
            __Vdly__normalizer__DOT__hangul_divider__DOT__divider__DOT__quotient_work = 0U;
            vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__iterations = 0U;
            vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__divisor 
                = ((0x11U == (IData)(vlSelf->__PVT__normalizer__DOT__state))
                    ? 0x24cU : 0x1cU);
            vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__remainder_work = 0ULL;
            vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__zero_divisor 
                = (0U == ((0x11U == (IData)(vlSelf->__PVT__normalizer__DOT__state))
                           ? 0x24cU : 0x1cU));
            __Vdly__normalizer__DOT__hangul_divider__DOT__divider__DOT__state = 1U;
        }
        if ((8U & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
            if ((4U & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
                vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__failed = 1U;
                vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__code = 0x11U;
                __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 0xaU;
            } else if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
                    vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__failed = 1U;
                    vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__code = 0x11U;
                    __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 0xaU;
                } else if (((IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_valid) 
                            & ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                               & (4U == (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__state))))) {
                    __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 0U;
                }
            } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
                VL_ASSIGNSEL_WI(128,32,(0x7fU & VL_SHIFTL_III(7,32,32, (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__word_index), 5U)), vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data, vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__read_data);
                if ((3U == (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__word_index))) {
                    __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 0xaU;
                } else {
                    vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__word_index 
                        = (3U & ((IData)(1U) + (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__word_index)));
                    __Vtemp_5[0U] = 4U;
                    __Vtemp_5[1U] = 0U;
                    __Vtemp_5[2U] = 0U;
                    VL_ADD_W(3, __Vtemp_6, __Vtemp_5, vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value);
                    __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[0U] 
                        = __Vtemp_6[0U];
                    __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[1U] 
                        = __Vtemp_6[1U];
                    __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[2U] 
                        = (3U & __Vtemp_6[2U]);
                    __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 5U;
                }
            } else if ((((IData)(vlSelf->__PVT__normalizer__DOT__classify_selected) 
                         & (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT____Vcellinp__span__DOT__normalization__tbl_rsp_valid)) 
                        & (IData)(vlSelf->__PVT__normalizer__DOT__class_tbl_ready))) {
                if (vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer_rsp_error) {
                    vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__failed = 1U;
                    vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__code = 4U;
                    __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 0xaU;
                } else {
                    vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__read_data 
                        = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer_rsp_data;
                    __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 9U;
                }
            }
        } else if ((4U & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
            if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
                    if (((IData)(vlSelf->__PVT__normalizer__DOT__class_tbl_valid) 
                         & ((IData)(vlSelf->__PVT__normalizer__DOT__classify_selected) 
                            & (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT____Vcellinp__span__DOT__normalization__tbl_req_ready)))) {
                        __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 8U;
                    }
                } else if ((IData)(((0U != vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__request_address[2U]) 
                                    | VL_GTE_W(3, vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__request_address, vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__table_end)))) {
                    vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__failed = 1U;
                    vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__code = 0x11U;
                    __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 0xaU;
                } else {
                    __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 7U;
                }
            } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
                VL_ADD_W(3, __Vtemp_8, vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__data_start, vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value);
                vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__request_address[0U] 
                    = __Vtemp_8[0U];
                vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__request_address[1U] 
                    = __Vtemp_8[1U];
                vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__request_address[2U] 
                    = (3U & __Vtemp_8[2U]);
                __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 6U;
            } else if ((IData)(((((0ULL != (3ULL & vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__base)) 
                                  | (0U != vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__data_start[2U])) 
                                 | (0U != vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__table_end[2U])) 
                                | ((0U == vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__count) 
                                   | (vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__index 
                                      >= vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__count))))) {
                vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__failed = 1U;
                vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__code = 0x11U;
                __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 0xaU;
            } else {
                __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 5U;
            }
        } else if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
            if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
                __Vtemp_10[0U] = vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__count;
                __Vtemp_10[1U] = 0U;
                __Vtemp_10[2U] = 0U;
                VL_SHIFTL_WWI(66,66,32, __Vtemp_11, __Vtemp_10, 4U);
                VL_ADD_W(3, __Vtemp_12, vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__data_start, __Vtemp_11);
                vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__table_end[0U] 
                    = __Vtemp_12[0U];
                vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__table_end[1U] 
                    = __Vtemp_12[1U];
                vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__table_end[2U] 
                    = (3U & __Vtemp_12[2U]);
                __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 4U;
            } else {
                __Vtemp_14[0U] = 0x20U;
                __Vtemp_14[1U] = 0U;
                __Vtemp_14[2U] = 0U;
                __Vtemp_15[0U] = (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__base);
                __Vtemp_15[1U] = (IData)((vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__base 
                                          >> 0x20U));
                __Vtemp_15[2U] = 0U;
                VL_ADD_W(3, __Vtemp_16, __Vtemp_14, __Vtemp_15);
                vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__data_start[0U] 
                    = __Vtemp_16[0U];
                vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__data_start[1U] 
                    = __Vtemp_16[1U];
                vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__data_start[2U] 
                    = (3U & __Vtemp_16[2U]);
                __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 3U;
            }
        } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
            __Vtemp_18[0U] = vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__index;
            __Vtemp_18[1U] = 0U;
            __Vtemp_18[2U] = 0U;
            VL_SHIFTL_WWI(66,66,32, __Vtemp_19, __Vtemp_18, 4U);
            __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[0U] 
                = __Vtemp_19[0U];
            __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[1U] 
                = __Vtemp_19[1U];
            __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[2U] 
                = (3U & __Vtemp_19[2U]);
            __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 2U;
        } else if ((((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                     & (3U == (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__state))) 
                    & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__reader_ready))) {
            vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__word_index = 0U;
            vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__base 
                = vlSelf->__PVT__normalizer__DOT__classification__DOT__base;
            vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__count 
                = vlSelf->__PVT__normalizer__DOT__classification__DOT__range_count;
            vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__index 
                = vlSelf->__PVT__normalizer__DOT__classification__DOT__middle;
            vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[0U] = 0U;
            vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[1U] = 0U;
            vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[2U] = 0U;
            vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[3U] = 0U;
            vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__failed = 0U;
            vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__code = 0U;
            __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 1U;
        }
        if ((0x20U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
            if ((0x10U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                vlSelf->__PVT__normalizer__DOT__code = 0x12U;
                __Vdly__normalizer__DOT__state = 0x26U;
            } else if ((8U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                vlSelf->__PVT__normalizer__DOT__code = 0x12U;
                __Vdly__normalizer__DOT__state = 0x26U;
            } else if ((4U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                    if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                        vlSelf->__PVT__normalizer__DOT__code = 0x12U;
                        __Vdly__normalizer__DOT__state = 0x26U;
                    } else {
                        __Vdly__normalizer__DOT__state = 0x26U;
                    }
                } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                    if (((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                         & (1U == (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__state)))) {
                        if (vlSymsp->TOP.bench__DOT__boot_done) {
                            __Vdly__normalizer__DOT__mode = 0U;
                            vlSelf->__PVT__normalizer__DOT__ranges_base 
                                = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_ranges_base;
                            __Vdly__normalizer__DOT__decomposition_base 
                                = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_decomposition_base;
                            __Vdly__normalizer__DOT__scalar_pool_base 
                                = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_scalar_pool_base;
                            __Vdly__normalizer__DOT__composition_base 
                                = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_composition_base;
                            vlSelf->__PVT__normalizer__DOT__range_count 
                                = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_range_count;
                            vlSelf->__PVT__normalizer__DOT__class_count 
                                = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_class_count;
                            __Vdly__normalizer__DOT__decomposition_count 
                                = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_decomposition_count;
                            __Vdly__normalizer__DOT__scalar_pool_count 
                                = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_scalar_pool_count;
                            __Vdly__normalizer__DOT__composition_count 
                                = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_composition_count;
                            __Vdly__normalizer__DOT__scalar_count = 0U;
                            __Vdly__normalizer__DOT__output_index = 0U;
                            vlSelf->__PVT__normalizer__DOT__code = 0U;
                            __Vdly__normalizer__DOT__state = 1U;
                        } else {
                            vlSelf->__PVT__normalizer__DOT__code = 6U;
                            __Vdly__normalizer__DOT__state = 0x26U;
                        }
                    }
                } else if (((IData)(vlSelf->out_valid) 
                            & ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                               & (3U == (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__state))))) {
                    if (vlSelf->out_last) {
                        __Vdly__normalizer__DOT__state = 0x25U;
                    } else {
                        __Vdly__normalizer__DOT__output_index 
                            = ((IData)(1U) + vlSelf->__PVT__normalizer__DOT__output_index);
                    }
                }
            } else if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                    if (vlSelf->__PVT__normalizer__DOT__divider_valid) {
                        if (vlSelf->__PVT__normalizer__DOT__divider_zero) {
                            vlSelf->__PVT__normalizer__DOT__code = 0x12U;
                            __Vdly__normalizer__DOT__state = 0x26U;
                        } else if ((0U == vlSelf->__PVT__normalizer__DOT__remainder_value)) {
                            __Vdly__normalizer__DOT__composite_scalar 
                                = (vlSelf->__PVT__normalizer__DOT__starter_scalar 
                                   + (vlSelf->__PVT__normalizer__DOT__current_scalar 
                                      - (IData)(0x11a7U)));
                            __Vdly__normalizer__DOT__state = 0x1cU;
                        } else {
                            __Vdly__normalizer__DOT__state = 0x18U;
                        }
                    }
                } else if (vlSelf->__PVT__normalizer__DOT__divider_ready) {
                    __Vdly__normalizer__DOT__state = 0x23U;
                }
            } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                __Vdly__normalizer__DOT__composite_scalar 
                    = ((IData)(0xac00U) + vlSelf->__PVT__normalizer__DOT__hangul_product);
                __Vdly__normalizer__DOT__state = 0x1cU;
            } else {
                __Vdly__normalizer__DOT__hangul_product 
                    = (VL_SHIFTL_III(32,32,32, vlSelf->__PVT__normalizer__DOT__hangul_product, 5U) 
                       - VL_SHIFTL_III(32,32,32, vlSelf->__PVT__normalizer__DOT__hangul_product, 2U));
                __Vdly__normalizer__DOT__state = 0x21U;
            }
        } else if ((0x10U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
            if ((8U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                if ((4U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                    if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                        if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                            __Vdly__normalizer__DOT__hangul_product 
                                = (vlSelf->__PVT__normalizer__DOT__hangul_product 
                                   + vlSelf->__PVT__normalizer__DOT__hangul_v_index);
                            __Vdly__normalizer__DOT__state = 0x20U;
                        } else {
                            __Vdly__normalizer__DOT__hangul_product 
                                = (vlSelf->__PVT__normalizer__DOT__hangul_product 
                                   + vlSelf->__PVT__normalizer__DOT__hangul_l_index);
                            __Vdly__normalizer__DOT__state = 0x1fU;
                        }
                    } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                        __Vdly__normalizer__DOT__hangul_product 
                            = (VL_SHIFTL_III(32,32,32, vlSelf->__PVT__normalizer__DOT__hangul_l_index, 4U) 
                               + VL_SHIFTL_III(32,32,32, vlSelf->__PVT__normalizer__DOT__hangul_l_index, 2U));
                        __Vdly__normalizer__DOT__state = 0x1eU;
                    } else {
                        __Vdly__normalizer__DOT__read_index 
                            = ((IData)(1U) + vlSelf->__PVT__normalizer__DOT__read_index);
                        __Vdlyvval__normalizer__DOT__scalars__v0 
                            = vlSelf->__PVT__normalizer__DOT__composite_scalar;
                        __Vdlyvset__normalizer__DOT__scalars__v0 = 1U;
                        __Vdlyvdim0__normalizer__DOT__scalars__v0 
                            = (0xfU & vlSelf->__PVT__normalizer__DOT__starter_position);
                        __Vdly__normalizer__DOT__state = 0x16U;
                        __Vdly__normalizer__DOT__starter_scalar 
                            = vlSelf->__PVT__normalizer__DOT__composite_scalar;
                    }
                } else if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                    if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                        __Vdly__normalizer__DOT__read_index 
                            = ((IData)(1U) + vlSelf->__PVT__normalizer__DOT__read_index);
                        __Vdlyvval__normalizer__DOT__scalars__v1 
                            = vlSelf->__PVT__normalizer__DOT__current_scalar;
                        __Vdlyvset__normalizer__DOT__scalars__v1 = 1U;
                        __Vdlyvdim0__normalizer__DOT__scalars__v1 
                            = (0xfU & vlSelf->__PVT__normalizer__DOT__write_index);
                        __Vdly__normalizer__DOT__last_ccc 
                            = vlSelf->__PVT__normalizer__DOT__current_ccc;
                        __Vdly__normalizer__DOT__state = 0x16U;
                        __Vdlyvval__normalizer__DOT__combining_classes__v0 
                            = vlSelf->__PVT__normalizer__DOT__current_ccc;
                        __Vdlyvset__normalizer__DOT__combining_classes__v0 = 1U;
                        __Vdlyvdim0__normalizer__DOT__combining_classes__v0 
                            = (0xfU & vlSelf->__PVT__normalizer__DOT__write_index);
                        if ((0U == (IData)(vlSelf->__PVT__normalizer__DOT__current_ccc))) {
                            __Vdly__normalizer__DOT__starter_valid = 1U;
                            __Vdly__normalizer__DOT__starter_scalar 
                                = vlSelf->__PVT__normalizer__DOT__current_scalar;
                            vlSelf->__PVT__normalizer__DOT__starter_position 
                                = vlSelf->__PVT__normalizer__DOT__write_index;
                        }
                        __Vdly__normalizer__DOT__write_index 
                            = ((IData)(1U) + vlSelf->__PVT__normalizer__DOT__write_index);
                    } else if ((1U & ((((((~ (IData)(vlSelf->__PVT__normalizer__DOT__record_scalar_valid)) 
                                          | (0x10ffffU 
                                             < vlSelf->__PVT__normalizer__DOT__record_value[1U])) 
                                         | ((0xd800U 
                                             <= vlSelf->__PVT__normalizer__DOT__record_value[1U]) 
                                            & (0xdfffU 
                                               >= vlSelf->__PVT__normalizer__DOT__record_value[1U]))) 
                                        | (0x10ffffU 
                                           < vlSelf->__PVT__normalizer__DOT__record_value[2U])) 
                                       | ((0xd800U 
                                           <= vlSelf->__PVT__normalizer__DOT__record_value[2U]) 
                                          & (0xdfffU 
                                             >= vlSelf->__PVT__normalizer__DOT__record_value[2U]))) 
                                      | (0U != vlSelf->__PVT__normalizer__DOT__record_value[3U])))) {
                        vlSelf->__PVT__normalizer__DOT__code = 0x12U;
                        __Vdly__normalizer__DOT__state = 0x26U;
                    } else if (vlSelf->__PVT__normalizer__DOT__composition_equal) {
                        __Vdly__normalizer__DOT__composite_scalar 
                            = vlSelf->__PVT__normalizer__DOT__record_value[2U];
                        __Vdly__normalizer__DOT__state = 0x1cU;
                    } else {
                        if (vlSelf->__PVT__normalizer__DOT__composition_before) {
                            __Vdly__normalizer__DOT__search_low 
                                = ((IData)(1U) + vlSelf->__PVT__normalizer__DOT__search_middle);
                        } else {
                            __Vdly__normalizer__DOT__search_high 
                                = vlSelf->__PVT__normalizer__DOT__search_middle;
                        }
                        __Vdly__normalizer__DOT__state = 0x19U;
                    }
                } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                    if ((vlSelf->__PVT__normalizer__DOT__search_low 
                         >= vlSelf->__PVT__normalizer__DOT__search_high)) {
                        __Vdly__normalizer__DOT__state = 0x1bU;
                    } else {
                        __Vdly__normalizer__DOT__search_middle 
                            = (vlSelf->__PVT__normalizer__DOT__search_low 
                               + VL_SHIFTR_III(32,32,32, 
                                               (vlSelf->__PVT__normalizer__DOT__search_high 
                                                - vlSelf->__PVT__normalizer__DOT__search_low), 1U));
                        __Vdly__normalizer__DOT__state = 4U;
                    }
                } else {
                    __Vdly__normalizer__DOT__search_low = 0U;
                    __Vdly__normalizer__DOT__search_high 
                        = vlSelf->__PVT__normalizer__DOT__composition_count;
                    __Vdly__normalizer__DOT__reading_composition = 1U;
                    __Vdly__normalizer__DOT__state = 0x19U;
                }
            } else if ((4U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                    if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                        if ((1U & ((~ (IData)(vlSelf->__PVT__normalizer__DOT__starter_valid)) 
                                   | (~ ((0U == (IData)(vlSelf->__PVT__normalizer__DOT__last_ccc)) 
                                         | ((IData)(vlSelf->__PVT__normalizer__DOT__last_ccc) 
                                            < (IData)(vlSelf->__PVT__normalizer__DOT__current_ccc))))))) {
                            __Vdly__normalizer__DOT__state = 0x1bU;
                        } else if (((((0x1100U <= vlSelf->__PVT__normalizer__DOT__starter_scalar) 
                                      & (0x1112U >= vlSelf->__PVT__normalizer__DOT__starter_scalar)) 
                                     & (0x1161U <= vlSelf->__PVT__normalizer__DOT__current_scalar)) 
                                    & (0x1175U >= vlSelf->__PVT__normalizer__DOT__current_scalar))) {
                            vlSelf->__PVT__normalizer__DOT__hangul_l_index 
                                = (vlSelf->__PVT__normalizer__DOT__starter_scalar 
                                   - (IData)(0x1100U));
                            vlSelf->__PVT__normalizer__DOT__hangul_v_index 
                                = (vlSelf->__PVT__normalizer__DOT__current_scalar 
                                   - (IData)(0x1161U));
                            __Vdly__normalizer__DOT__state = 0x1dU;
                        } else {
                            __Vdly__normalizer__DOT__state 
                                = (((((0xac00U <= vlSelf->__PVT__normalizer__DOT__starter_scalar) 
                                      & (0xd7a3U >= vlSelf->__PVT__normalizer__DOT__starter_scalar)) 
                                     & (0x11a7U < vlSelf->__PVT__normalizer__DOT__current_scalar)) 
                                    & (0x11c2U >= vlSelf->__PVT__normalizer__DOT__current_scalar))
                                    ? 0x22U : 0x18U);
                        }
                    } else if ((vlSelf->__PVT__normalizer__DOT__read_index 
                                == vlSelf->__PVT__normalizer__DOT__scalar_count)) {
                        __Vdly__normalizer__DOT__scalar_count 
                            = vlSelf->__PVT__normalizer__DOT__write_index;
                        __Vdly__normalizer__DOT__output_index = 0U;
                        __Vdly__normalizer__DOT__state = 0x24U;
                    } else {
                        vlSelf->__PVT__normalizer__DOT__current_scalar 
                            = vlSelf->__PVT__normalizer__DOT__scalars
                            [(0xfU & vlSelf->__PVT__normalizer__DOT__read_index)];
                        __Vdly__normalizer__DOT__state = 0x17U;
                        vlSelf->__PVT__normalizer__DOT__current_ccc 
                            = vlSelf->__PVT__normalizer__DOT__combining_classes
                            [(0xfU & vlSelf->__PVT__normalizer__DOT__read_index)];
                    }
                } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                    __Vdly__normalizer__DOT__read_index = 0U;
                    __Vdly__normalizer__DOT__write_index = 0U;
                    __Vdly__normalizer__DOT__starter_valid = 0U;
                    __Vdly__normalizer__DOT__last_ccc = 0U;
                    __Vdly__normalizer__DOT__state = 0x16U;
                } else if (vlSelf->__PVT__normalizer__DOT__divider_valid) {
                    if (vlSelf->__PVT__normalizer__DOT__divider_zero) {
                        vlSelf->__PVT__normalizer__DOT__code = 0x12U;
                        __Vdly__normalizer__DOT__state = 0x26U;
                    } else {
                        __Vdly__normalizer__DOT__hangul_v 
                            = ((IData)(0x1161U) + vlSelf->__PVT__normalizer__DOT__quotient);
                        __Vdly__normalizer__DOT__hangul_t 
                            = ((IData)(0x11a7U) + vlSelf->__PVT__normalizer__DOT__remainder_value);
                        __Vdly__normalizer__DOT__append_scalar 
                            = vlSelf->__PVT__normalizer__DOT__hangul_l;
                        __Vdly__normalizer__DOT__append_source = 2U;
                        __Vdly__normalizer__DOT__hangul_part = 0U;
                        __Vdly__normalizer__DOT__state = 9U;
                    }
                }
            } else if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                    if (vlSelf->__PVT__normalizer__DOT__divider_ready) {
                        __Vdly__normalizer__DOT__state = 0x14U;
                    }
                } else if (vlSelf->__PVT__normalizer__DOT__divider_valid) {
                    if (vlSelf->__PVT__normalizer__DOT__divider_zero) {
                        vlSelf->__PVT__normalizer__DOT__code = 0x12U;
                        __Vdly__normalizer__DOT__state = 0x26U;
                    } else {
                        vlSelf->__PVT__normalizer__DOT__hangul_l 
                            = ((IData)(0x1100U) + vlSelf->__PVT__normalizer__DOT__quotient);
                        vlSelf->__PVT__normalizer__DOT__hangul_index 
                            = vlSelf->__PVT__normalizer__DOT__remainder_value;
                        __Vdly__normalizer__DOT__state = 0x13U;
                    }
                }
            } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                if (vlSelf->__PVT__normalizer__DOT__divider_ready) {
                    __Vdly__normalizer__DOT__state = 0x12U;
                }
            } else if (vlSelf->__PVT__normalizer__DOT__input_last) {
                if (((1U == vlSelf->__PVT__normalizer__DOT__mode) 
                     | (2U == vlSelf->__PVT__normalizer__DOT__mode))) {
                    __Vdly__normalizer__DOT__state = 0x15U;
                } else {
                    __Vdly__normalizer__DOT__output_index = 0U;
                    __Vdly__normalizer__DOT__state = 0x24U;
                }
            } else {
                __Vdly__normalizer__DOT__state = 1U;
            }
        } else if ((8U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
            if ((4U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                    if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                        if (((1U == (IData)(vlSelf->__PVT__normalizer__DOT__append_source)) 
                             & (1U < vlSelf->__PVT__normalizer__DOT__pool_remaining))) {
                            __Vdly__normalizer__DOT__pool_cursor 
                                = ((IData)(1U) + vlSelf->__PVT__normalizer__DOT__pool_cursor);
                            vlSelf->__PVT__normalizer__DOT__pool_remaining 
                                = (vlSelf->__PVT__normalizer__DOT__pool_remaining 
                                   - (IData)(1U));
                            __Vdly__normalizer__DOT__state = 7U;
                        } else if (((2U == (IData)(vlSelf->__PVT__normalizer__DOT__append_source)) 
                                    & (0U == (IData)(vlSelf->__PVT__normalizer__DOT__hangul_part)))) {
                            __Vdly__normalizer__DOT__append_scalar 
                                = vlSelf->__PVT__normalizer__DOT__hangul_v;
                            __Vdly__normalizer__DOT__hangul_part = 1U;
                            __Vdly__normalizer__DOT__state = 9U;
                        } else if ((((2U == (IData)(vlSelf->__PVT__normalizer__DOT__append_source)) 
                                     & (1U == (IData)(vlSelf->__PVT__normalizer__DOT__hangul_part))) 
                                    & (0x11a7U != vlSelf->__PVT__normalizer__DOT__hangul_t))) {
                            __Vdly__normalizer__DOT__append_scalar 
                                = vlSelf->__PVT__normalizer__DOT__hangul_t;
                            __Vdly__normalizer__DOT__hangul_part = 2U;
                            __Vdly__normalizer__DOT__state = 9U;
                        } else {
                            __Vdly__normalizer__DOT__state = 0x10U;
                        }
                    } else {
                        __Vdlyvval__normalizer__DOT__scalars__v2 
                            = vlSelf->__PVT__normalizer__DOT__append_scalar;
                        __Vdlyvset__normalizer__DOT__scalars__v2 = 1U;
                        __Vdlyvdim0__normalizer__DOT__scalars__v2 
                            = (0xfU & vlSelf->__PVT__normalizer__DOT__insert_position);
                        __Vdlyvval__normalizer__DOT__combining_classes__v1 
                            = vlSelf->__PVT__normalizer__DOT__append_ccc;
                        __Vdlyvdim0__normalizer__DOT__combining_classes__v1 
                            = (0xfU & vlSelf->__PVT__normalizer__DOT__insert_position);
                        __Vdly__normalizer__DOT__state = 0xfU;
                    }
                } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                    if (((IData)(vlSelf->__PVT__normalizer__DOT__previous_ccc) 
                         > (IData)(vlSelf->__PVT__normalizer__DOT__append_ccc))) {
                        __Vdlyvval__normalizer__DOT__scalars__v3 
                            = vlSelf->__PVT__normalizer__DOT__previous_scalar;
                        __Vdlyvset__normalizer__DOT__scalars__v3 = 1U;
                        __Vdlyvdim0__normalizer__DOT__scalars__v3 
                            = (0xfU & vlSelf->__PVT__normalizer__DOT__insert_position);
                        __Vdlyvval__normalizer__DOT__combining_classes__v2 
                            = vlSelf->__PVT__normalizer__DOT__previous_ccc;
                        __Vdlyvdim0__normalizer__DOT__combining_classes__v2 
                            = (0xfU & vlSelf->__PVT__normalizer__DOT__insert_position);
                        __Vdly__normalizer__DOT__insert_position 
                            = (vlSelf->__PVT__normalizer__DOT__insert_position 
                               - (IData)(1U));
                        __Vdly__normalizer__DOT__state 
                            = ((1U == vlSelf->__PVT__normalizer__DOT__insert_position)
                                ? 0xeU : 0xcU);
                    } else {
                        __Vdly__normalizer__DOT__state = 0xeU;
                    }
                } else {
                    vlSelf->__PVT__normalizer__DOT__previous_scalar 
                        = vlSelf->__PVT__normalizer__DOT__scalars
                        [(0xfU & (vlSelf->__PVT__normalizer__DOT__insert_position 
                                  - (IData)(1U)))];
                    __Vdly__normalizer__DOT__state = 0xdU;
                    vlSelf->__PVT__normalizer__DOT__previous_ccc 
                        = vlSelf->__PVT__normalizer__DOT__combining_classes
                        [(0xfU & (vlSelf->__PVT__normalizer__DOT__insert_position 
                                  - (IData)(1U)))];
                }
            } else if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                    if (vlSelf->__PVT__normalizer__DOT__class_valid) {
                        if (((IData)(vlSelf->__PVT__normalizer__DOT__class_valid) 
                             & (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__failed))) {
                            vlSelf->__PVT__normalizer__DOT__code 
                                = ((IData)(vlSelf->__PVT__normalizer__DOT__class_valid)
                                    ? (IData)(vlSelf->__PVT__normalizer__DOT__classification__DOT__code)
                                    : 0U);
                            __Vdly__normalizer__DOT__state = 0x26U;
                        } else {
                            vlSelf->__PVT__normalizer__DOT__append_ccc 
                                = (0xffU & vlSelf->__PVT__normalizer__DOT__class_properties);
                            __Vdly__normalizer__DOT__insert_position 
                                = vlSelf->__PVT__normalizer__DOT__scalar_count;
                            __Vdly__normalizer__DOT__scalar_count 
                                = ((IData)(1U) + vlSelf->__PVT__normalizer__DOT__scalar_count);
                            __Vdly__normalizer__DOT__state 
                                = (((0U == vlSelf->__PVT__normalizer__DOT__scalar_count) 
                                    | (0U == (0xffU 
                                              & vlSelf->__PVT__normalizer__DOT__class_properties)))
                                    ? 0xeU : 0xcU);
                        }
                    }
                } else if (vlSelf->__PVT__normalizer__DOT__class_ready) {
                    __Vdly__normalizer__DOT__state = 0xbU;
                }
            } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                if (((0x10ffffU < vlSelf->__PVT__normalizer__DOT__append_scalar) 
                     | ((0xd800U <= vlSelf->__PVT__normalizer__DOT__append_scalar) 
                        & (0xdfffU >= vlSelf->__PVT__normalizer__DOT__append_scalar)))) {
                    vlSelf->__PVT__normalizer__DOT__code = 0x12U;
                    __Vdly__normalizer__DOT__state = 0x26U;
                } else if ((0x10U <= vlSelf->__PVT__normalizer__DOT__scalar_count)) {
                    vlSelf->__PVT__normalizer__DOT__code = 0x30U;
                    __Vdly__normalizer__DOT__state = 0x26U;
                } else if ((0U == vlSelf->__PVT__normalizer__DOT__mode)) {
                    vlSelf->__PVT__normalizer__DOT__append_ccc = 0U;
                    __Vdly__normalizer__DOT__insert_position 
                        = vlSelf->__PVT__normalizer__DOT__scalar_count;
                    __Vdly__normalizer__DOT__state = 0xeU;
                    __Vdly__normalizer__DOT__scalar_count 
                        = ((IData)(1U) + vlSelf->__PVT__normalizer__DOT__scalar_count);
                } else {
                    __Vdly__normalizer__DOT__state = 0xaU;
                }
            } else if (vlSelf->__PVT__normalizer__DOT__pool_valid) {
                if (((IData)(vlSelf->__PVT__normalizer__DOT__pool_valid) 
                     & (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__failed))) {
                    vlSelf->__PVT__normalizer__DOT__code 
                        = ((IData)(vlSelf->__PVT__normalizer__DOT__pool_valid)
                            ? (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__code)
                            : 0U);
                    __Vdly__normalizer__DOT__state = 0x26U;
                } else {
                    __Vdly__normalizer__DOT__append_scalar 
                        = (((~ (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__failed)) 
                            & (IData)(vlSelf->__PVT__normalizer__DOT__pool_valid))
                            ? vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__result_data
                            : 0U);
                    __Vdly__normalizer__DOT__state = 9U;
                }
            }
        } else if ((4U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
            if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                    if (vlSelf->__PVT__normalizer__DOT__pool_ready) {
                        __Vdly__normalizer__DOT__state = 8U;
                    }
                } else if ((1U & (((((~ (IData)(vlSelf->__PVT__normalizer__DOT__record_scalar_valid)) 
                                     | (0U != (vlSelf->__PVT__normalizer__DOT__record_value[3U] 
                                               >> 1U))) 
                                    | (0U == vlSelf->__PVT__normalizer__DOT__record_value[2U])) 
                                   | (IData)((vlSelf->__PVT__normalizer__DOT__pool_end 
                                              >> 0x20U))) 
                                  | (vlSelf->__PVT__normalizer__DOT__pool_end 
                                     > (QData)((IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool_count)))))) {
                    vlSelf->__PVT__normalizer__DOT__code = 0x12U;
                    __Vdly__normalizer__DOT__state = 0x26U;
                } else if ((vlSelf->__PVT__normalizer__DOT__record_value[0U] 
                            < vlSelf->__PVT__normalizer__DOT__input_scalar)) {
                    __Vdly__normalizer__DOT__search_low 
                        = ((IData)(1U) + vlSelf->__PVT__normalizer__DOT__search_middle);
                    __Vdly__normalizer__DOT__state = 3U;
                } else if ((vlSelf->__PVT__normalizer__DOT__record_value[0U] 
                            > vlSelf->__PVT__normalizer__DOT__input_scalar)) {
                    __Vdly__normalizer__DOT__search_high 
                        = vlSelf->__PVT__normalizer__DOT__search_middle;
                    __Vdly__normalizer__DOT__state = 3U;
                } else if ((vlSelf->__PVT__normalizer__DOT__record_value[3U] 
                            & ((1U == vlSelf->__PVT__normalizer__DOT__mode) 
                               | (3U == vlSelf->__PVT__normalizer__DOT__mode)))) {
                    __Vdly__normalizer__DOT__append_scalar 
                        = vlSelf->__PVT__normalizer__DOT__input_scalar;
                    __Vdly__normalizer__DOT__append_source = 0U;
                    __Vdly__normalizer__DOT__state = 9U;
                } else {
                    __Vdly__normalizer__DOT__pool_cursor 
                        = vlSelf->__PVT__normalizer__DOT__record_value[1U];
                    vlSelf->__PVT__normalizer__DOT__pool_remaining 
                        = vlSelf->__PVT__normalizer__DOT__record_value[2U];
                    __Vdly__normalizer__DOT__append_source = 1U;
                    __Vdly__normalizer__DOT__state = 7U;
                }
            } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                if (vlSelf->__PVT__normalizer__DOT__record_valid) {
                    if (((IData)(vlSelf->__PVT__normalizer__DOT__record_valid) 
                         & (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__failed))) {
                        vlSelf->__PVT__normalizer__DOT__code 
                            = ((IData)(vlSelf->__PVT__normalizer__DOT__record_valid)
                                ? (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__code)
                                : 0U);
                        __Vdly__normalizer__DOT__state = 0x26U;
                    } else {
                        if (((~ (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__failed)) 
                             & (IData)(vlSelf->__PVT__normalizer__DOT__record_valid))) {
                            vlSelf->__PVT__normalizer__DOT__record_value[0U] 
                                = vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__result_data[0U];
                            vlSelf->__PVT__normalizer__DOT__record_value[1U] 
                                = vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__result_data[1U];
                            vlSelf->__PVT__normalizer__DOT__record_value[2U] 
                                = vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__result_data[2U];
                            vlSelf->__PVT__normalizer__DOT__record_value[3U] 
                                = vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__result_data[3U];
                        } else {
                            vlSelf->__PVT__normalizer__DOT__record_value[0U] = 0U;
                            vlSelf->__PVT__normalizer__DOT__record_value[1U] = 0U;
                            vlSelf->__PVT__normalizer__DOT__record_value[2U] = 0U;
                            vlSelf->__PVT__normalizer__DOT__record_value[3U] = 0U;
                        }
                        __Vdly__normalizer__DOT__state 
                            = ((IData)(vlSelf->__PVT__normalizer__DOT__reading_composition)
                                ? 0x1aU : 6U);
                    }
                }
            } else if (vlSelf->__PVT__normalizer__DOT__record_ready) {
                __Vdly__normalizer__DOT__state = 5U;
            }
        } else if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
            if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
                if ((vlSelf->__PVT__normalizer__DOT__search_low 
                     >= vlSelf->__PVT__normalizer__DOT__search_high)) {
                    __Vdly__normalizer__DOT__append_scalar 
                        = vlSelf->__PVT__normalizer__DOT__input_scalar;
                    __Vdly__normalizer__DOT__append_source = 0U;
                    __Vdly__normalizer__DOT__state = 9U;
                } else {
                    __Vdly__normalizer__DOT__search_middle 
                        = (vlSelf->__PVT__normalizer__DOT__search_low 
                           + VL_SHIFTR_III(32,32,32, 
                                           (vlSelf->__PVT__normalizer__DOT__search_high 
                                            - vlSelf->__PVT__normalizer__DOT__search_low), 1U));
                    __Vdly__normalizer__DOT__state = 4U;
                }
            } else {
                __Vdly__normalizer__DOT__search_low = 0U;
                __Vdly__normalizer__DOT__search_high 
                    = vlSelf->__PVT__normalizer__DOT__decomposition_count;
                __Vdly__normalizer__DOT__reading_composition = 0U;
                __Vdly__normalizer__DOT__state = 3U;
            }
        } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__state))) {
            if ((((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT____VdfgTmp_h115be047__0) 
                  & (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__in_valid)) 
                 & (IData)(vlSelf->in_ready))) {
                if (((0x10ffffU < vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalized_specials.out_value) 
                     | ((0xd800U <= vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalized_specials.out_value) 
                        & (0xdfffU >= vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalized_specials.out_value)))) {
                    vlSelf->__PVT__normalizer__DOT__code = 0x10U;
                    __Vdly__normalizer__DOT__state = 0x26U;
                } else {
                    vlSelf->__PVT__normalizer__DOT__input_scalar 
                        = vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalized_specials.out_value;
                    vlSelf->__PVT__normalizer__DOT__input_last 
                        = vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalized_specials.out_boundary;
                    __Vdly__normalizer__DOT__append_source = 0U;
                    __Vdly__normalizer__DOT__append_scalar 
                        = vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalized_specials.out_value;
                    if ((0U == vlSelf->__PVT__normalizer__DOT__mode)) {
                        __Vdly__normalizer__DOT__state = 9U;
                    } else if (((0xac00U <= vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalized_specials.out_value) 
                                & (0xd7a3U >= vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalized_specials.out_value))) {
                        vlSelf->__PVT__normalizer__DOT__hangul_index 
                            = (vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalized_specials.out_value 
                               - (IData)(0xac00U));
                        __Vdly__normalizer__DOT__state = 0x11U;
                    } else {
                        __Vdly__normalizer__DOT__state = 2U;
                    }
                }
            }
        } else if (((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                    & (1U == (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__state)))) {
            if (vlSymsp->TOP.bench__DOT__boot_done) {
                __Vdly__normalizer__DOT__mode = 0U;
                vlSelf->__PVT__normalizer__DOT__ranges_base 
                    = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_ranges_base;
                __Vdly__normalizer__DOT__decomposition_base 
                    = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_decomposition_base;
                __Vdly__normalizer__DOT__scalar_pool_base 
                    = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_scalar_pool_base;
                __Vdly__normalizer__DOT__composition_base 
                    = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_composition_base;
                vlSelf->__PVT__normalizer__DOT__range_count 
                    = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_range_count;
                vlSelf->__PVT__normalizer__DOT__class_count 
                    = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_class_count;
                __Vdly__normalizer__DOT__decomposition_count 
                    = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_decomposition_count;
                __Vdly__normalizer__DOT__scalar_pool_count 
                    = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_scalar_pool_count;
                __Vdly__normalizer__DOT__composition_count 
                    = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_composition_count;
                __Vdly__normalizer__DOT__scalar_count = 0U;
                __Vdly__normalizer__DOT__output_index = 0U;
                vlSelf->__PVT__normalizer__DOT__code = 0U;
                __Vdly__normalizer__DOT__state = 1U;
            } else {
                vlSelf->__PVT__normalizer__DOT__code = 6U;
                __Vdly__normalizer__DOT__state = 0x26U;
            }
        }
        if ((8U & (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__state))) {
            if ((4U & (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__state))) {
                vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__failed = 1U;
                vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__code = 0x11U;
                __Vdly__normalizer__DOT__records__DOT__reader__DOT__state = 0xaU;
            } else if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__state))) {
                    vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__failed = 1U;
                    vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__code = 0x11U;
                    __Vdly__normalizer__DOT__records__DOT__reader__DOT__state = 0xaU;
                } else if (((IData)(vlSelf->__PVT__normalizer__DOT__record_valid) 
                            & ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                               & (5U == (IData)(vlSelf->__PVT__normalizer__DOT__state))))) {
                    __Vdly__normalizer__DOT__records__DOT__reader__DOT__state = 0U;
                }
            } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__state))) {
                VL_ASSIGNSEL_WI(128,32,(0x7fU & VL_SHIFTL_III(7,32,32, (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__word_index), 5U)), vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__result_data, vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__read_data);
                if ((3U == (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__word_index))) {
                    __Vdly__normalizer__DOT__records__DOT__reader__DOT__state = 0xaU;
                } else {
                    vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__word_index 
                        = (3U & ((IData)(1U) + (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__word_index)));
                    __Vtemp_25[0U] = 4U;
                    __Vtemp_25[1U] = 0U;
                    __Vtemp_25[2U] = 0U;
                    VL_ADD_W(3, __Vtemp_26, __Vtemp_25, vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__offset_value);
                    __Vdly__normalizer__DOT__records__DOT__reader__DOT__offset_value[0U] 
                        = __Vtemp_26[0U];
                    __Vdly__normalizer__DOT__records__DOT__reader__DOT__offset_value[1U] 
                        = __Vtemp_26[1U];
                    __Vdly__normalizer__DOT__records__DOT__reader__DOT__offset_value[2U] 
                        = (3U & __Vtemp_26[2U]);
                    __Vdly__normalizer__DOT__records__DOT__reader__DOT__state = 5U;
                }
            } else if ((((IData)(vlSelf->__VdfgTmp_h0a1e14da__0) 
                         & (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT____Vcellinp__span__DOT__normalization__tbl_rsp_valid)) 
                        & (IData)(vlSelf->__PVT__normalizer__DOT__record_tbl_ready))) {
                if (vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer_rsp_error) {
                    vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__failed = 1U;
                    vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__code = 4U;
                    __Vdly__normalizer__DOT__records__DOT__reader__DOT__state = 0xaU;
                } else {
                    vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__read_data 
                        = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer_rsp_data;
                    __Vdly__normalizer__DOT__records__DOT__reader__DOT__state = 9U;
                }
            }
        } else if ((4U & (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__state))) {
            if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__state))) {
                    if (((IData)(vlSelf->__PVT__normalizer__DOT__record_tbl_valid) 
                         & ((IData)(vlSelf->__VdfgTmp_h0a1e14da__0) 
                            & (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT____Vcellinp__span__DOT__normalization__tbl_req_ready)))) {
                        __Vdly__normalizer__DOT__records__DOT__reader__DOT__state = 8U;
                    }
                } else if ((IData)(((0U != vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__request_address[2U]) 
                                    | VL_GTE_W(3, vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__request_address, vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__table_end)))) {
                    vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__failed = 1U;
                    vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__code = 0x11U;
                    __Vdly__normalizer__DOT__records__DOT__reader__DOT__state = 0xaU;
                } else {
                    __Vdly__normalizer__DOT__records__DOT__reader__DOT__state = 7U;
                }
            } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__state))) {
                VL_ADD_W(3, __Vtemp_28, vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__data_start, vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__offset_value);
                vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__request_address[0U] 
                    = __Vtemp_28[0U];
                vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__request_address[1U] 
                    = __Vtemp_28[1U];
                vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__request_address[2U] 
                    = (3U & __Vtemp_28[2U]);
                __Vdly__normalizer__DOT__records__DOT__reader__DOT__state = 6U;
            } else if ((IData)(((((0ULL != (3ULL & vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__base)) 
                                  | (0U != vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__data_start[2U])) 
                                 | (0U != vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__table_end[2U])) 
                                | ((0U == vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__count) 
                                   | (vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__index 
                                      >= vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__count))))) {
                vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__failed = 1U;
                vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__code = 0x11U;
                __Vdly__normalizer__DOT__records__DOT__reader__DOT__state = 0xaU;
            } else {
                __Vdly__normalizer__DOT__records__DOT__reader__DOT__state = 5U;
            }
        } else if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__state))) {
            if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__state))) {
                __Vtemp_30[0U] = vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__count;
                __Vtemp_30[1U] = 0U;
                __Vtemp_30[2U] = 0U;
                VL_SHIFTL_WWI(66,66,32, __Vtemp_31, __Vtemp_30, 4U);
                VL_ADD_W(3, __Vtemp_32, vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__data_start, __Vtemp_31);
                vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__table_end[0U] 
                    = __Vtemp_32[0U];
                vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__table_end[1U] 
                    = __Vtemp_32[1U];
                vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__table_end[2U] 
                    = (3U & __Vtemp_32[2U]);
                __Vdly__normalizer__DOT__records__DOT__reader__DOT__state = 4U;
            } else {
                __Vtemp_34[0U] = 0x20U;
                __Vtemp_34[1U] = 0U;
                __Vtemp_34[2U] = 0U;
                __Vtemp_35[0U] = (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__base);
                __Vtemp_35[1U] = (IData)((vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__base 
                                          >> 0x20U));
                __Vtemp_35[2U] = 0U;
                VL_ADD_W(3, __Vtemp_36, __Vtemp_34, __Vtemp_35);
                vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__data_start[0U] 
                    = __Vtemp_36[0U];
                vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__data_start[1U] 
                    = __Vtemp_36[1U];
                vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__data_start[2U] 
                    = (3U & __Vtemp_36[2U]);
                __Vdly__normalizer__DOT__records__DOT__reader__DOT__state = 3U;
            }
        } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__state))) {
            __Vtemp_38[0U] = vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__index;
            __Vtemp_38[1U] = 0U;
            __Vtemp_38[2U] = 0U;
            VL_SHIFTL_WWI(66,66,32, __Vtemp_39, __Vtemp_38, 4U);
            __Vdly__normalizer__DOT__records__DOT__reader__DOT__offset_value[0U] 
                = __Vtemp_39[0U];
            __Vdly__normalizer__DOT__records__DOT__reader__DOT__offset_value[1U] 
                = __Vtemp_39[1U];
            __Vdly__normalizer__DOT__records__DOT__reader__DOT__offset_value[2U] 
                = (3U & __Vtemp_39[2U]);
            __Vdly__normalizer__DOT__records__DOT__reader__DOT__state = 2U;
        } else if ((((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                     & (4U == (IData)(vlSelf->__PVT__normalizer__DOT__state))) 
                    & (IData)(vlSelf->__PVT__normalizer__DOT__record_ready))) {
            vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__word_index = 0U;
            if (vlSelf->__PVT__normalizer__DOT__reading_composition) {
                vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__base 
                    = vlSelf->__PVT__normalizer__DOT__composition_base;
                vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__count 
                    = vlSelf->__PVT__normalizer__DOT__composition_count;
            } else {
                vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__base 
                    = vlSelf->__PVT__normalizer__DOT__decomposition_base;
                vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__count 
                    = vlSelf->__PVT__normalizer__DOT__decomposition_count;
            }
            vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__index 
                = vlSelf->__PVT__normalizer__DOT__search_middle;
            vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__result_data[0U] = 0U;
            vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__result_data[1U] = 0U;
            vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__result_data[2U] = 0U;
            vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__result_data[3U] = 0U;
            vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__failed = 0U;
            vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__code = 0U;
            __Vdly__normalizer__DOT__records__DOT__reader__DOT__state = 1U;
        }
        if ((8U & (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__state))) {
            if ((4U & (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__state))) {
                vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__failed = 1U;
                vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__code = 0x11U;
                __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state = 0xaU;
            } else if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__state))) {
                    vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__failed = 1U;
                    vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__code = 0x11U;
                    __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state = 0xaU;
                } else if (((IData)(vlSelf->__PVT__normalizer__DOT__pool_valid) 
                            & ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                               & (8U == (IData)(vlSelf->__PVT__normalizer__DOT__state))))) {
                    __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state = 0U;
                }
            } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__state))) {
                vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__result_data 
                    = (((~ ((IData)(0xffffffffU) << 
                            (0x1fU & VL_SHIFTL_III(5,32,32, (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__word_index), 5U)))) 
                        & vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__result_data) 
                       | (0xffffffffULL & (vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__read_data 
                                           << (0x1fU 
                                               & VL_SHIFTL_III(5,32,32, (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__word_index), 5U)))));
                if (vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__word_index) {
                    vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__word_index 
                        = (1U & ((IData)(1U) + (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__word_index)));
                    __Vtemp_42[0U] = 4U;
                    __Vtemp_42[1U] = 0U;
                    __Vtemp_42[2U] = 0U;
                    VL_ADD_W(3, __Vtemp_43, __Vtemp_42, vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value);
                    __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value[0U] 
                        = __Vtemp_43[0U];
                    __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value[1U] 
                        = __Vtemp_43[1U];
                    __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value[2U] 
                        = (3U & __Vtemp_43[2U]);
                    __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state = 5U;
                } else {
                    __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state = 0xaU;
                }
            } else if ((((IData)(vlSelf->__PVT__normalizer__DOT__pool_selected) 
                         & (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT____Vcellinp__span__DOT__normalization__tbl_rsp_valid)) 
                        & (IData)(vlSelf->__PVT__normalizer__DOT__pool_tbl_ready))) {
                if (vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer_rsp_error) {
                    vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__failed = 1U;
                    vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__code = 4U;
                    __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state = 0xaU;
                } else {
                    vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__read_data 
                        = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer_rsp_data;
                    __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state = 9U;
                }
            }
        } else if ((4U & (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__state))) {
            if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__state))) {
                    if (((IData)(vlSelf->__PVT__normalizer__DOT__pool_tbl_valid) 
                         & ((IData)(vlSelf->__PVT__normalizer__DOT__pool_selected) 
                            & (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT____Vcellinp__span__DOT__normalization__tbl_req_ready)))) {
                        __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state = 8U;
                    }
                } else if ((IData)(((0U != vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__request_address[2U]) 
                                    | VL_GTE_W(3, vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__request_address, vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__table_end)))) {
                    vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__failed = 1U;
                    vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__code = 0x11U;
                    __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state = 0xaU;
                } else {
                    __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state = 7U;
                }
            } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__state))) {
                VL_ADD_W(3, __Vtemp_45, vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__data_start, vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value);
                vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__request_address[0U] 
                    = __Vtemp_45[0U];
                vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__request_address[1U] 
                    = __Vtemp_45[1U];
                vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__request_address[2U] 
                    = (3U & __Vtemp_45[2U]);
                __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state = 6U;
            } else if ((IData)(((((0ULL != (3ULL & vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__base)) 
                                  | (0U != vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__data_start[2U])) 
                                 | (0U != vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__table_end[2U])) 
                                | ((0U == vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__count) 
                                   | (vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__index 
                                      >= vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__count))))) {
                vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__failed = 1U;
                vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__code = 0x11U;
                __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state = 0xaU;
            } else {
                __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state = 5U;
            }
        } else if ((2U & (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__state))) {
            if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__state))) {
                __Vtemp_47[0U] = vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__count;
                __Vtemp_47[1U] = 0U;
                __Vtemp_47[2U] = 0U;
                VL_SHIFTL_WWI(66,66,32, __Vtemp_48, __Vtemp_47, 2U);
                VL_ADD_W(3, __Vtemp_49, vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__data_start, __Vtemp_48);
                vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__table_end[0U] 
                    = __Vtemp_49[0U];
                vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__table_end[1U] 
                    = __Vtemp_49[1U];
                vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__table_end[2U] 
                    = (3U & __Vtemp_49[2U]);
                __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state = 4U;
            } else {
                __Vtemp_51[0U] = 0x20U;
                __Vtemp_51[1U] = 0U;
                __Vtemp_51[2U] = 0U;
                __Vtemp_52[0U] = (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__base);
                __Vtemp_52[1U] = (IData)((vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__base 
                                          >> 0x20U));
                __Vtemp_52[2U] = 0U;
                VL_ADD_W(3, __Vtemp_53, __Vtemp_51, __Vtemp_52);
                vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__data_start[0U] 
                    = __Vtemp_53[0U];
                vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__data_start[1U] 
                    = __Vtemp_53[1U];
                vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__data_start[2U] 
                    = (3U & __Vtemp_53[2U]);
                __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state = 3U;
            }
        } else if ((1U & (IData)(vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__state))) {
            __Vtemp_55[0U] = vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__index;
            __Vtemp_55[1U] = 0U;
            __Vtemp_55[2U] = 0U;
            VL_SHIFTL_WWI(66,66,32, __Vtemp_56, __Vtemp_55, 2U);
            __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value[0U] 
                = __Vtemp_56[0U];
            __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value[1U] 
                = __Vtemp_56[1U];
            __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value[2U] 
                = (3U & __Vtemp_56[2U]);
            __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state = 2U;
        } else if ((((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                     & (7U == (IData)(vlSelf->__PVT__normalizer__DOT__state))) 
                    & (IData)(vlSelf->__PVT__normalizer__DOT__pool_ready))) {
            vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__word_index = 0U;
            vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__base 
                = vlSelf->__PVT__normalizer__DOT__scalar_pool_base;
            vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__count 
                = vlSelf->__PVT__normalizer__DOT__scalar_pool_count;
            vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__index 
                = vlSelf->__PVT__normalizer__DOT__pool_cursor;
            vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__result_data = 0U;
            vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__failed = 0U;
            vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__code = 0U;
            __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state = 1U;
        }
    } else {
        __Vdly__normalizer__DOT__classification__DOT__state = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__admitted = 0U;
        __Vdly__normalizer__DOT__classification__DOT__failed = 0U;
        __Vdly__normalizer__DOT__classification__DOT__code = 0U;
        __Vdly__normalizer__DOT__classification__DOT__base = 0ULL;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__scalar = 0U;
        __Vdly__normalizer__DOT__classification__DOT__range_count = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__class_count = 0U;
        __Vdly__normalizer__DOT__classification__DOT__low_index = 0U;
        __Vdly__normalizer__DOT__classification__DOT__high_index = 0U;
        __Vdly__normalizer__DOT__classification__DOT__middle = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__first_scalar = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__last_scalar = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__class_value = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__property_value = 0U;
        vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__dividend_shift = 0U;
        __Vdly__normalizer__DOT__hangul_divider__DOT__divider__DOT__quotient_work = 0U;
        vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__iterations = 0U;
        __Vdly__normalizer__DOT__hangul_divider__DOT__divider__DOT__state = 0U;
        vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__divisor = 0U;
        vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__remainder_work = 0ULL;
        vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__quotient_result = 0U;
        vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__remainder_result = 0U;
        vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__zero_divisor = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__word_index = 0U;
        __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[0U] = 0U;
        __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[1U] = 0U;
        __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[2U] = 0U;
        __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__base = 0ULL;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__count = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__index = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__data_start[0U] = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__data_start[1U] = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__data_start[2U] = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__table_end[0U] = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__table_end[1U] = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__table_end[2U] = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__request_address[0U] = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__request_address[1U] = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__request_address[2U] = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[0U] = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[1U] = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[2U] = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[3U] = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__read_data = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__failed = 0U;
        vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__code = 0U;
        __Vdly__normalizer__DOT__pool_cursor = 0U;
        vlSelf->__PVT__normalizer__DOT__pool_remaining = 0U;
        __Vdly__normalizer__DOT__hangul_product = 0U;
        __Vdly__normalizer__DOT__read_index = 0U;
        __Vdly__normalizer__DOT__write_index = 0U;
        __Vdly__normalizer__DOT__state = 0U;
        __Vdly__normalizer__DOT__mode = 0U;
        __Vdly__normalizer__DOT__scalar_count = 0U;
        vlSelf->__PVT__normalizer__DOT__input_scalar = 0U;
        __Vdly__normalizer__DOT__append_scalar = 0U;
        __Vdly__normalizer__DOT__insert_position = 0U;
        vlSelf->__PVT__normalizer__DOT__input_last = 0U;
        __Vdly__normalizer__DOT__append_source = 0U;
        __Vdly__normalizer__DOT__hangul_part = 0U;
        vlSelf->__PVT__normalizer__DOT__append_ccc = 0U;
        vlSelf->__PVT__normalizer__DOT__previous_ccc = 0U;
        vlSelf->__PVT__normalizer__DOT__previous_scalar = 0U;
        vlSelf->__PVT__normalizer__DOT__ranges_base = 0ULL;
        __Vdly__normalizer__DOT__decomposition_base = 0ULL;
        __Vdly__normalizer__DOT__scalar_pool_base = 0ULL;
        __Vdly__normalizer__DOT__composition_base = 0ULL;
        vlSelf->__PVT__normalizer__DOT__range_count = 0U;
        vlSelf->__PVT__normalizer__DOT__class_count = 0U;
        __Vdly__normalizer__DOT__decomposition_count = 0U;
        __Vdly__normalizer__DOT__scalar_pool_count = 0U;
        __Vdly__normalizer__DOT__composition_count = 0U;
        __Vdly__normalizer__DOT__search_low = 0U;
        __Vdly__normalizer__DOT__search_high = 0U;
        __Vdly__normalizer__DOT__search_middle = 0U;
        __Vdly__normalizer__DOT__reading_composition = 0U;
        vlSelf->__PVT__normalizer__DOT__record_value[0U] = 0U;
        vlSelf->__PVT__normalizer__DOT__record_value[1U] = 0U;
        vlSelf->__PVT__normalizer__DOT__record_value[2U] = 0U;
        vlSelf->__PVT__normalizer__DOT__record_value[3U] = 0U;
        vlSelf->__PVT__normalizer__DOT__hangul_index = 0U;
        vlSelf->__PVT__normalizer__DOT__hangul_l = 0U;
        __Vdly__normalizer__DOT__hangul_v = 0U;
        __Vdly__normalizer__DOT__hangul_t = 0U;
        vlSelf->__PVT__normalizer__DOT__hangul_l_index = 0U;
        vlSelf->__PVT__normalizer__DOT__hangul_v_index = 0U;
        __Vdly__normalizer__DOT__output_index = 0U;
        vlSelf->__PVT__normalizer__DOT__current_scalar = 0U;
        __Vdly__normalizer__DOT__starter_scalar = 0U;
        vlSelf->__PVT__normalizer__DOT__starter_position = 0U;
        __Vdly__normalizer__DOT__composite_scalar = 0U;
        vlSelf->__PVT__normalizer__DOT__current_ccc = 0U;
        __Vdly__normalizer__DOT__last_ccc = 0U;
        __Vdly__normalizer__DOT__starter_valid = 0U;
        vlSelf->__PVT__normalizer__DOT__code = 0U;
        vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__word_index = 0U;
        __Vdly__normalizer__DOT__records__DOT__reader__DOT__offset_value[0U] = 0U;
        __Vdly__normalizer__DOT__records__DOT__reader__DOT__offset_value[1U] = 0U;
        __Vdly__normalizer__DOT__records__DOT__reader__DOT__offset_value[2U] = 0U;
        __Vdly__normalizer__DOT__records__DOT__reader__DOT__state = 0U;
        vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__base = 0ULL;
        vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__count = 0U;
        vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__index = 0U;
        vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__data_start[0U] = 0U;
        vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__data_start[1U] = 0U;
        vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__data_start[2U] = 0U;
        vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__table_end[0U] = 0U;
        vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__table_end[1U] = 0U;
        vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__table_end[2U] = 0U;
        vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__request_address[0U] = 0U;
        vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__request_address[1U] = 0U;
        vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__request_address[2U] = 0U;
        vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__result_data[0U] = 0U;
        vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__result_data[1U] = 0U;
        vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__result_data[2U] = 0U;
        vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__result_data[3U] = 0U;
        vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__read_data = 0U;
        vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__failed = 0U;
        vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__code = 0U;
        vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__word_index = 0U;
        __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value[0U] = 0U;
        __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value[1U] = 0U;
        __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value[2U] = 0U;
        __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state = 0U;
        vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__base = 0ULL;
        vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__count = 0U;
        vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__index = 0U;
        vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__data_start[0U] = 0U;
        vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__data_start[1U] = 0U;
        vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__data_start[2U] = 0U;
        vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__table_end[0U] = 0U;
        vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__table_end[1U] = 0U;
        vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__table_end[2U] = 0U;
        vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__request_address[0U] = 0U;
        vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__request_address[1U] = 0U;
        vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__request_address[2U] = 0U;
        vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__result_data = 0U;
        vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__read_data = 0U;
        vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__failed = 0U;
        vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__code = 0U;
    }
    vlSelf->__PVT__normalizer__DOT__classification__DOT__high_index 
        = __Vdly__normalizer__DOT__classification__DOT__high_index;
    vlSelf->__PVT__normalizer__DOT__classification__DOT__low_index 
        = __Vdly__normalizer__DOT__classification__DOT__low_index;
    vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__quotient_work 
        = __Vdly__normalizer__DOT__hangul_divider__DOT__divider__DOT__quotient_work;
    vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__state 
        = __Vdly__normalizer__DOT__hangul_divider__DOT__divider__DOT__state;
    vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__shifted_remainder 
        = (0x1ffffffffULL & (VL_SHIFTL_QQI(33,33,32, vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__remainder_work, 1U) 
                             | (QData)((IData)((vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__dividend_shift 
                                                >> 0x1fU)))));
    vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[0U] 
        = __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[0U];
    vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[1U] 
        = __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[1U];
    vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[2U] 
        = __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[2U];
    vlSelf->__PVT__normalizer__DOT__classification__DOT__base 
        = __Vdly__normalizer__DOT__classification__DOT__base;
    vlSelf->__PVT__normalizer__DOT__classification__DOT__range_count 
        = __Vdly__normalizer__DOT__classification__DOT__range_count;
    vlSelf->__PVT__normalizer__DOT__classification__DOT__middle 
        = __Vdly__normalizer__DOT__classification__DOT__middle;
    vlSelf->__PVT__normalizer__DOT__classification__DOT__state 
        = __Vdly__normalizer__DOT__classification__DOT__state;
    vlSelf->__PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state 
        = __Vdly__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state;
    vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__subtract 
        = (vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__shifted_remainder 
           >= (QData)((IData)(vlSelf->__PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__divisor)));
    vlSelf->__PVT__normalizer__DOT__classification__DOT__code 
        = __Vdly__normalizer__DOT__classification__DOT__code;
    vlSelf->__PVT__normalizer__DOT__mode = __Vdly__normalizer__DOT__mode;
    vlSelf->__PVT__normalizer__DOT__composite_scalar 
        = __Vdly__normalizer__DOT__composite_scalar;
    vlSelf->__PVT__normalizer__DOT__hangul_product 
        = __Vdly__normalizer__DOT__hangul_product;
    vlSelf->__PVT__normalizer__DOT__read_index = __Vdly__normalizer__DOT__read_index;
    vlSelf->__PVT__normalizer__DOT__last_ccc = __Vdly__normalizer__DOT__last_ccc;
    vlSelf->__PVT__normalizer__DOT__starter_valid = __Vdly__normalizer__DOT__starter_valid;
    vlSelf->__PVT__normalizer__DOT__write_index = __Vdly__normalizer__DOT__write_index;
    vlSelf->__PVT__normalizer__DOT__search_low = __Vdly__normalizer__DOT__search_low;
    vlSelf->__PVT__normalizer__DOT__search_high = __Vdly__normalizer__DOT__search_high;
    vlSelf->__PVT__normalizer__DOT__hangul_v = __Vdly__normalizer__DOT__hangul_v;
    vlSelf->__PVT__normalizer__DOT__hangul_t = __Vdly__normalizer__DOT__hangul_t;
    vlSelf->__PVT__normalizer__DOT__append_source = __Vdly__normalizer__DOT__append_source;
    vlSelf->__PVT__normalizer__DOT__hangul_part = __Vdly__normalizer__DOT__hangul_part;
    vlSelf->__PVT__normalizer__DOT__append_scalar = __Vdly__normalizer__DOT__append_scalar;
    vlSelf->__PVT__normalizer__DOT__insert_position 
        = __Vdly__normalizer__DOT__insert_position;
    vlSelf->__PVT__normalizer__DOT__classification__DOT__failed 
        = __Vdly__normalizer__DOT__classification__DOT__failed;
    vlSelf->__PVT__normalizer__DOT__scalar_count = __Vdly__normalizer__DOT__scalar_count;
    vlSelf->__PVT__normalizer__DOT__output_index = __Vdly__normalizer__DOT__output_index;
    vlSelf->__PVT__normalizer__DOT__starter_scalar 
        = __Vdly__normalizer__DOT__starter_scalar;
    if (__Vdlyvset__normalizer__DOT__combining_classes__v0) {
        vlSelf->__PVT__normalizer__DOT__combining_classes[__Vdlyvdim0__normalizer__DOT__combining_classes__v0] 
            = __Vdlyvval__normalizer__DOT__combining_classes__v0;
    }
    if (__Vdlyvset__normalizer__DOT__scalars__v2) {
        vlSelf->__PVT__normalizer__DOT__combining_classes[__Vdlyvdim0__normalizer__DOT__combining_classes__v1] 
            = __Vdlyvval__normalizer__DOT__combining_classes__v1;
    }
    if (__Vdlyvset__normalizer__DOT__scalars__v0) {
        vlSelf->__PVT__normalizer__DOT__scalars[__Vdlyvdim0__normalizer__DOT__scalars__v0] 
            = __Vdlyvval__normalizer__DOT__scalars__v0;
    }
    if (__Vdlyvset__normalizer__DOT__scalars__v1) {
        vlSelf->__PVT__normalizer__DOT__scalars[__Vdlyvdim0__normalizer__DOT__scalars__v1] 
            = __Vdlyvval__normalizer__DOT__scalars__v1;
    }
    if (__Vdlyvset__normalizer__DOT__scalars__v2) {
        vlSelf->__PVT__normalizer__DOT__scalars[__Vdlyvdim0__normalizer__DOT__scalars__v2] 
            = __Vdlyvval__normalizer__DOT__scalars__v2;
    }
    if (__Vdlyvset__normalizer__DOT__scalars__v3) {
        vlSelf->__PVT__normalizer__DOT__combining_classes[__Vdlyvdim0__normalizer__DOT__combining_classes__v2] 
            = __Vdlyvval__normalizer__DOT__combining_classes__v2;
        vlSelf->__PVT__normalizer__DOT__scalars[__Vdlyvdim0__normalizer__DOT__scalars__v3] 
            = __Vdlyvval__normalizer__DOT__scalars__v3;
    }
    vlSelf->__PVT__normalizer__DOT__record_scalar_valid 
        = ((~ ((0xd800U <= vlSelf->__PVT__normalizer__DOT__record_value[0U]) 
               & (0xdfffU >= vlSelf->__PVT__normalizer__DOT__record_value[0U]))) 
           & (0x10ffffU >= vlSelf->__PVT__normalizer__DOT__record_value[0U]));
    vlSelf->__PVT__normalizer__DOT__pool_end = (0x1ffffffffULL 
                                                & ((QData)((IData)(
                                                                   vlSelf->__PVT__normalizer__DOT__record_value[1U])) 
                                                   + (QData)((IData)(
                                                                     vlSelf->__PVT__normalizer__DOT__record_value[2U]))));
    __VdfgTmp_hd39cf095__0 = (vlSelf->__PVT__normalizer__DOT__record_value[0U] 
                              == vlSelf->__PVT__normalizer__DOT__starter_scalar);
    vlSelf->__PVT__normalizer__DOT__composition_equal 
        = ((IData)(__VdfgTmp_hd39cf095__0) & (vlSelf->__PVT__normalizer__DOT__record_value[1U] 
                                              == vlSelf->__PVT__normalizer__DOT__current_scalar));
    vlSelf->__PVT__normalizer__DOT__composition_before 
        = ((vlSelf->__PVT__normalizer__DOT__record_value[0U] 
            < vlSelf->__PVT__normalizer__DOT__starter_scalar) 
           | ((IData)(__VdfgTmp_hd39cf095__0) & (vlSelf->__PVT__normalizer__DOT__record_value[1U] 
                                                 < vlSelf->__PVT__normalizer__DOT__current_scalar)));
    vlSelf->__PVT__normalizer__DOT__composition_base 
        = __Vdly__normalizer__DOT__composition_base;
    vlSelf->__PVT__normalizer__DOT__decomposition_base 
        = __Vdly__normalizer__DOT__decomposition_base;
    vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__offset_value[0U] 
        = __Vdly__normalizer__DOT__records__DOT__reader__DOT__offset_value[0U];
    vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__offset_value[1U] 
        = __Vdly__normalizer__DOT__records__DOT__reader__DOT__offset_value[1U];
    vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__offset_value[2U] 
        = __Vdly__normalizer__DOT__records__DOT__reader__DOT__offset_value[2U];
    vlSelf->__PVT__normalizer__DOT__reading_composition 
        = __Vdly__normalizer__DOT__reading_composition;
    vlSelf->__PVT__normalizer__DOT__composition_count 
        = __Vdly__normalizer__DOT__composition_count;
    vlSelf->__PVT__normalizer__DOT__decomposition_count 
        = __Vdly__normalizer__DOT__decomposition_count;
    vlSelf->__PVT__normalizer__DOT__search_middle = __Vdly__normalizer__DOT__search_middle;
    vlSelf->__PVT__normalizer__DOT__records__DOT__reader__DOT__state 
        = __Vdly__normalizer__DOT__records__DOT__reader__DOT__state;
    vlSelf->__PVT__normalizer__DOT__scalar_pool_base 
        = __Vdly__normalizer__DOT__scalar_pool_base;
    vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value[0U] 
        = __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value[0U];
    vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value[1U] 
        = __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value[1U];
    vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value[2U] 
        = __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value[2U];
    vlSelf->__PVT__normalizer__DOT__scalar_pool_count 
        = __Vdly__normalizer__DOT__scalar_pool_count;
    vlSelf->__PVT__normalizer__DOT__pool_cursor = __Vdly__normalizer__DOT__pool_cursor;
    vlSelf->__PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__state 
        = __Vdly__normalizer__DOT__scalar_pool__DOT__reader__DOT__state;
    vlSelf->__PVT__normalizer__DOT__state = __Vdly__normalizer__DOT__state;
    vlSelf->__PVT__normalizer__DOT__classify_selected 
        = ((0xaU == (IData)(vlSelf->__PVT__normalizer__DOT__state)) 
           | (0xbU == (IData)(vlSelf->__PVT__normalizer__DOT__state)));
    vlSelf->__PVT__normalizer__DOT__pool_selected = 
        ((7U == (IData)(vlSelf->__PVT__normalizer__DOT__state)) 
         | (8U == (IData)(vlSelf->__PVT__normalizer__DOT__state)));
    vlSelf->__VdfgTmp_h0a1e14da__0 = (1U & ((~ (IData)(vlSelf->__PVT__normalizer__DOT__classify_selected)) 
                                            & (~ (IData)(vlSelf->__PVT__normalizer__DOT__pool_selected))));
}
