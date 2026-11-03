// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vbench.h for the primary calling header

#include "Vbench__pch.h"
#include "Vbench__Syms.h"
#include "Vbench_anvil_edge_special_splitter__pi7.h"

VL_INLINE_OPT void Vbench_anvil_edge_special_splitter__pi7___act_comb__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__raw_specials__0(Vbench_anvil_edge_special_splitter__pi7* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+            Vbench_anvil_edge_special_splitter__pi7___act_comb__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__raw_specials__0\n"); );
    // Body
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
}

VL_INLINE_OPT void Vbench_anvil_edge_special_splitter__pi7___nba_sequent__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__raw_specials__0(Vbench_anvil_edge_special_splitter__pi7* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+            Vbench_anvil_edge_special_splitter__pi7___nba_sequent__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__raw_specials__0\n"); );
    // Init
    IData/*31:0*/ __VdfgTmp_hb6edd8f3__0;
    __VdfgTmp_hb6edd8f3__0 = 0;
    CData/*5:0*/ __Vdly__splitter__DOT__state;
    __Vdly__splitter__DOT__state = 0;
    CData/*0:0*/ __Vdly__splitter__DOT__output_last;
    __Vdly__splitter__DOT__output_last = 0;
    IData/*31:0*/ __Vdly__splitter__DOT__scalar_count;
    __Vdly__splitter__DOT__scalar_count = 0;
    IData/*31:0*/ __Vdly__splitter__DOT__scalar_index;
    __Vdly__splitter__DOT__scalar_index = 0;
    IData/*31:0*/ __Vdly__splitter__DOT__byte_count;
    __Vdly__splitter__DOT__byte_count = 0;
    IData/*31:0*/ __Vdly__splitter__DOT__scan_index;
    __Vdly__splitter__DOT__scan_index = 0;
    IData/*31:0*/ __Vdly__splitter__DOT__plan_count;
    __Vdly__splitter__DOT__plan_count = 0;
    IData/*31:0*/ __Vdly__splitter__DOT__output_index;
    __Vdly__splitter__DOT__output_index = 0;
    CData/*3:0*/ __Vdlyvdim0__splitter__DOT__plan_value__v0;
    __Vdlyvdim0__splitter__DOT__plan_value__v0 = 0;
    IData/*31:0*/ __Vdlyvval__splitter__DOT__plan_value__v0;
    __Vdlyvval__splitter__DOT__plan_value__v0 = 0;
    CData/*0:0*/ __Vdlyvset__splitter__DOT__plan_value__v0;
    __Vdlyvset__splitter__DOT__plan_value__v0 = 0;
    CData/*3:0*/ __Vdlyvdim0__splitter__DOT__plan_special__v0;
    __Vdlyvdim0__splitter__DOT__plan_special__v0 = 0;
    CData/*0:0*/ __Vdlyvset__splitter__DOT__plan_special__v0;
    __Vdlyvset__splitter__DOT__plan_special__v0 = 0;
    CData/*3:0*/ __Vdlyvdim0__splitter__DOT__plan_space__v0;
    __Vdlyvdim0__splitter__DOT__plan_space__v0 = 0;
    CData/*0:0*/ __Vdlyvval__splitter__DOT__plan_space__v0;
    __Vdlyvval__splitter__DOT__plan_space__v0 = 0;
    CData/*3:0*/ __Vdlyvdim0__splitter__DOT__plan_value__v1;
    __Vdlyvdim0__splitter__DOT__plan_value__v1 = 0;
    IData/*31:0*/ __Vdlyvval__splitter__DOT__plan_value__v1;
    __Vdlyvval__splitter__DOT__plan_value__v1 = 0;
    CData/*0:0*/ __Vdlyvset__splitter__DOT__plan_value__v1;
    __Vdlyvset__splitter__DOT__plan_value__v1 = 0;
    CData/*3:0*/ __Vdlyvdim0__splitter__DOT__plan_special__v1;
    __Vdlyvdim0__splitter__DOT__plan_special__v1 = 0;
    CData/*0:0*/ __Vdlyvset__splitter__DOT__plan_special__v1;
    __Vdlyvset__splitter__DOT__plan_special__v1 = 0;
    CData/*3:0*/ __Vdlyvdim0__splitter__DOT__plan_space__v1;
    __Vdlyvdim0__splitter__DOT__plan_space__v1 = 0;
    IData/*31:0*/ __Vdly__splitter__DOT__cursor;
    __Vdly__splitter__DOT__cursor = 0;
    IData/*31:0*/ __Vdly__splitter__DOT__edge_cursor;
    __Vdly__splitter__DOT__edge_cursor = 0;
    IData/*31:0*/ __Vdly__splitter__DOT__edge_first;
    __Vdly__splitter__DOT__edge_first = 0;
    CData/*3:0*/ __Vdlyvdim0__splitter__DOT__bytes_memory__v0;
    __Vdlyvdim0__splitter__DOT__bytes_memory__v0 = 0;
    CData/*7:0*/ __Vdlyvval__splitter__DOT__bytes_memory__v0;
    __Vdlyvval__splitter__DOT__bytes_memory__v0 = 0;
    CData/*0:0*/ __Vdlyvset__splitter__DOT__bytes_memory__v0;
    __Vdlyvset__splitter__DOT__bytes_memory__v0 = 0;
    CData/*3:0*/ __Vdlyvdim0__splitter__DOT__byte_ends__v0;
    __Vdlyvdim0__splitter__DOT__byte_ends__v0 = 0;
    IData/*31:0*/ __Vdlyvval__splitter__DOT__byte_ends__v0;
    __Vdlyvval__splitter__DOT__byte_ends__v0 = 0;
    CData/*2:0*/ __Vdly__splitter__DOT__encoded_remaining;
    __Vdly__splitter__DOT__encoded_remaining = 0;
    CData/*3:0*/ __Vdlyvdim0__splitter__DOT__scalar_starts__v0;
    __Vdlyvdim0__splitter__DOT__scalar_starts__v0 = 0;
    IData/*31:0*/ __Vdlyvval__splitter__DOT__scalar_starts__v0;
    __Vdlyvval__splitter__DOT__scalar_starts__v0 = 0;
    CData/*0:0*/ __Vdlyvset__splitter__DOT__scalar_starts__v0;
    __Vdlyvset__splitter__DOT__scalar_starts__v0 = 0;
    CData/*3:0*/ __Vdlyvdim0__splitter__DOT__properties__v0;
    __Vdlyvdim0__splitter__DOT__properties__v0 = 0;
    SData/*9:0*/ __Vdlyvval__splitter__DOT__properties__v0;
    __Vdlyvval__splitter__DOT__properties__v0 = 0;
    CData/*0:0*/ __Vdlyvset__splitter__DOT__properties__v0;
    __Vdlyvset__splitter__DOT__properties__v0 = 0;
    CData/*3:0*/ __Vdlyvdim0__splitter__DOT__scalars__v0;
    __Vdlyvdim0__splitter__DOT__scalars__v0 = 0;
    IData/*31:0*/ __Vdlyvval__splitter__DOT__scalars__v0;
    __Vdlyvval__splitter__DOT__scalars__v0 = 0;
    CData/*0:0*/ __Vdlyvset__splitter__DOT__scalars__v0;
    __Vdlyvset__splitter__DOT__scalars__v0 = 0;
    CData/*3:0*/ __Vdly__splitter__DOT__classification__DOT__state;
    __Vdly__splitter__DOT__classification__DOT__state = 0;
    IData/*31:0*/ __Vdly__splitter__DOT__classification__DOT__high_index;
    __Vdly__splitter__DOT__classification__DOT__high_index = 0;
    IData/*31:0*/ __Vdly__splitter__DOT__classification__DOT__low_index;
    __Vdly__splitter__DOT__classification__DOT__low_index = 0;
    IData/*31:0*/ __Vdly__splitter__DOT__classification__DOT__middle;
    __Vdly__splitter__DOT__classification__DOT__middle = 0;
    QData/*63:0*/ __Vdly__splitter__DOT__classification__DOT__base;
    __Vdly__splitter__DOT__classification__DOT__base = 0;
    IData/*31:0*/ __Vdly__splitter__DOT__classification__DOT__range_count;
    __Vdly__splitter__DOT__classification__DOT__range_count = 0;
    CData/*3:0*/ __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state;
    __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 0;
    VlWide<3>/*65:0*/ __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value;
    VL_ZERO_W(66, __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value);
    CData/*2:0*/ __Vdly__splitter__DOT__encoder__DOT__state;
    __Vdly__splitter__DOT__encoder__DOT__state = 0;
    CData/*2:0*/ __Vdly__splitter__DOT__encoder__DOT__remaining;
    __Vdly__splitter__DOT__encoder__DOT__remaining = 0;
    IData/*31:0*/ __Vdly__splitter__DOT__encoder__DOT__encoded;
    __Vdly__splitter__DOT__encoder__DOT__encoded = 0;
    CData/*0:0*/ __Vdly__splitter__DOT__encoder__DOT__final_scalar;
    __Vdly__splitter__DOT__encoder__DOT__final_scalar = 0;
    CData/*3:0*/ __Vdly__splitter__DOT__records__DOT__reader__DOT__state;
    __Vdly__splitter__DOT__records__DOT__reader__DOT__state = 0;
    VlWide<3>/*65:0*/ __Vdly__splitter__DOT__records__DOT__reader__DOT__offset_value;
    VL_ZERO_W(66, __Vdly__splitter__DOT__records__DOT__reader__DOT__offset_value);
    CData/*3:0*/ __Vdly__splitter__DOT__edges__DOT__reader__DOT__state;
    __Vdly__splitter__DOT__edges__DOT__reader__DOT__state = 0;
    VlWide<3>/*65:0*/ __Vdly__splitter__DOT__edges__DOT__reader__DOT__offset_value;
    VL_ZERO_W(66, __Vdly__splitter__DOT__edges__DOT__reader__DOT__offset_value);
    VlWide<3>/*95:0*/ __Vtemp_3;
    VlWide<3>/*95:0*/ __Vtemp_4;
    VlWide<3>/*95:0*/ __Vtemp_6;
    VlWide<3>/*95:0*/ __Vtemp_8;
    VlWide<3>/*95:0*/ __Vtemp_9;
    VlWide<3>/*95:0*/ __Vtemp_10;
    VlWide<3>/*95:0*/ __Vtemp_12;
    VlWide<3>/*95:0*/ __Vtemp_13;
    VlWide<3>/*95:0*/ __Vtemp_14;
    VlWide<3>/*95:0*/ __Vtemp_16;
    VlWide<3>/*95:0*/ __Vtemp_17;
    VlWide<3>/*95:0*/ __Vtemp_20;
    VlWide<3>/*95:0*/ __Vtemp_21;
    VlWide<3>/*95:0*/ __Vtemp_23;
    VlWide<3>/*95:0*/ __Vtemp_25;
    VlWide<3>/*95:0*/ __Vtemp_26;
    VlWide<3>/*95:0*/ __Vtemp_27;
    VlWide<3>/*95:0*/ __Vtemp_29;
    VlWide<3>/*95:0*/ __Vtemp_30;
    VlWide<3>/*95:0*/ __Vtemp_31;
    VlWide<3>/*95:0*/ __Vtemp_33;
    VlWide<3>/*95:0*/ __Vtemp_34;
    VlWide<3>/*95:0*/ __Vtemp_37;
    VlWide<3>/*95:0*/ __Vtemp_38;
    VlWide<3>/*95:0*/ __Vtemp_40;
    VlWide<3>/*95:0*/ __Vtemp_42;
    VlWide<3>/*95:0*/ __Vtemp_43;
    VlWide<3>/*95:0*/ __Vtemp_44;
    VlWide<3>/*95:0*/ __Vtemp_46;
    VlWide<3>/*95:0*/ __Vtemp_47;
    VlWide<3>/*95:0*/ __Vtemp_48;
    VlWide<3>/*95:0*/ __Vtemp_50;
    VlWide<3>/*95:0*/ __Vtemp_51;
    // Body
    __Vdly__splitter__DOT__encoder__DOT__final_scalar 
        = vlSelf->__PVT__splitter__DOT__encoder__DOT__final_scalar;
    __Vdly__splitter__DOT__encoder__DOT__encoded = vlSelf->__PVT__splitter__DOT__encoder__DOT__encoded;
    __Vdly__splitter__DOT__encoder__DOT__remaining 
        = vlSelf->__PVT__splitter__DOT__encoder__DOT__remaining;
    __Vdly__splitter__DOT__encoder__DOT__state = vlSelf->__PVT__splitter__DOT__encoder__DOT__state;
    __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[0U] 
        = vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[0U];
    __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[1U] 
        = vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[1U];
    __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[2U] 
        = vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[2U];
    __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state 
        = vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state;
    __Vdly__splitter__DOT__edges__DOT__reader__DOT__offset_value[0U] 
        = vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__offset_value[0U];
    __Vdly__splitter__DOT__edges__DOT__reader__DOT__offset_value[1U] 
        = vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__offset_value[1U];
    __Vdly__splitter__DOT__edges__DOT__reader__DOT__offset_value[2U] 
        = vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__offset_value[2U];
    __Vdly__splitter__DOT__edges__DOT__reader__DOT__state 
        = vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__state;
    __Vdly__splitter__DOT__classification__DOT__range_count 
        = vlSelf->__PVT__splitter__DOT__classification__DOT__range_count;
    __Vdly__splitter__DOT__classification__DOT__base 
        = vlSelf->__PVT__splitter__DOT__classification__DOT__base;
    __Vdly__splitter__DOT__classification__DOT__middle 
        = vlSelf->__PVT__splitter__DOT__classification__DOT__middle;
    __Vdly__splitter__DOT__classification__DOT__low_index 
        = vlSelf->__PVT__splitter__DOT__classification__DOT__low_index;
    __Vdly__splitter__DOT__classification__DOT__high_index 
        = vlSelf->__PVT__splitter__DOT__classification__DOT__high_index;
    __Vdly__splitter__DOT__classification__DOT__state 
        = vlSelf->__PVT__splitter__DOT__classification__DOT__state;
    __Vdly__splitter__DOT__encoded_remaining = vlSelf->__PVT__splitter__DOT__encoded_remaining;
    __Vdly__splitter__DOT__edge_cursor = vlSelf->__PVT__splitter__DOT__edge_cursor;
    __Vdly__splitter__DOT__output_index = vlSelf->__PVT__splitter__DOT__output_index;
    __Vdly__splitter__DOT__plan_count = vlSelf->__PVT__splitter__DOT__plan_count;
    __Vdly__splitter__DOT__byte_count = vlSelf->__PVT__splitter__DOT__byte_count;
    __Vdly__splitter__DOT__output_last = vlSelf->__PVT__splitter__DOT__output_last;
    __Vdlyvset__splitter__DOT__scalar_starts__v0 = 0U;
    __Vdly__splitter__DOT__edge_first = vlSelf->__PVT__splitter__DOT__edge_first;
    __Vdly__splitter__DOT__scalar_index = vlSelf->__PVT__splitter__DOT__scalar_index;
    __Vdlyvset__splitter__DOT__plan_value__v0 = 0U;
    __Vdlyvset__splitter__DOT__plan_value__v1 = 0U;
    __Vdlyvset__splitter__DOT__scalars__v0 = 0U;
    __Vdlyvset__splitter__DOT__plan_special__v0 = 0U;
    __Vdlyvset__splitter__DOT__plan_special__v1 = 0U;
    __Vdly__splitter__DOT__scan_index = vlSelf->__PVT__splitter__DOT__scan_index;
    __Vdly__splitter__DOT__scalar_count = vlSelf->__PVT__splitter__DOT__scalar_count;
    __Vdlyvset__splitter__DOT__properties__v0 = 0U;
    __Vdlyvset__splitter__DOT__bytes_memory__v0 = 0U;
    __Vdly__splitter__DOT__cursor = vlSelf->__PVT__splitter__DOT__cursor;
    __Vdly__splitter__DOT__state = vlSelf->__PVT__splitter__DOT__state;
    __Vdly__splitter__DOT__records__DOT__reader__DOT__offset_value[0U] 
        = vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__offset_value[0U];
    __Vdly__splitter__DOT__records__DOT__reader__DOT__offset_value[1U] 
        = vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__offset_value[1U];
    __Vdly__splitter__DOT__records__DOT__reader__DOT__offset_value[2U] 
        = vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__offset_value[2U];
    __Vdly__splitter__DOT__records__DOT__reader__DOT__state 
        = vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__state;
    if (vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) {
        if ((8U & (IData)(vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__state))) {
            if ((4U & (IData)(vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__state))) {
                vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__failed = 1U;
                vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__code = 0x11U;
                __Vdly__splitter__DOT__records__DOT__reader__DOT__state = 0xaU;
            } else if ((2U & (IData)(vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__state))) {
                    vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__failed = 1U;
                    vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__code = 0x11U;
                    __Vdly__splitter__DOT__records__DOT__reader__DOT__state = 0xaU;
                } else if (((IData)(vlSelf->__PVT__splitter__DOT__record_valid) 
                            & ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                               & ((9U == (IData)(vlSelf->__PVT__splitter__DOT__state)) 
                                  | (0xcU == (IData)(vlSelf->__PVT__splitter__DOT__state)))))) {
                    __Vdly__splitter__DOT__records__DOT__reader__DOT__state = 0U;
                }
            } else if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__state))) {
                VL_ASSIGNSEL_WI(128,32,(0x7fU & VL_SHIFTL_III(7,32,32, (IData)(vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__word_index), 5U)), vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__result_data, vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__read_data);
                if ((3U == (IData)(vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__word_index))) {
                    __Vdly__splitter__DOT__records__DOT__reader__DOT__state = 0xaU;
                } else {
                    vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__word_index 
                        = (3U & ((IData)(1U) + (IData)(vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__word_index)));
                    __Vtemp_3[0U] = 4U;
                    __Vtemp_3[1U] = 0U;
                    __Vtemp_3[2U] = 0U;
                    VL_ADD_W(3, __Vtemp_4, __Vtemp_3, vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__offset_value);
                    __Vdly__splitter__DOT__records__DOT__reader__DOT__offset_value[0U] 
                        = __Vtemp_4[0U];
                    __Vdly__splitter__DOT__records__DOT__reader__DOT__offset_value[1U] 
                        = __Vtemp_4[1U];
                    __Vdly__splitter__DOT__records__DOT__reader__DOT__offset_value[2U] 
                        = (3U & __Vtemp_4[2U]);
                    __Vdly__splitter__DOT__records__DOT__reader__DOT__state = 5U;
                }
            } else if ((((IData)(vlSelf->__VdfgTmp_hed1c005a__0) 
                         & (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__raw_specials__tbl_rsp_valid)) 
                        & (IData)(vlSelf->__PVT__splitter__DOT__record_rsp_ready))) {
                if (vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer_rsp_error) {
                    vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__failed = 1U;
                    vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__code = 4U;
                    __Vdly__splitter__DOT__records__DOT__reader__DOT__state = 0xaU;
                } else {
                    vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__read_data 
                        = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer_rsp_data;
                    __Vdly__splitter__DOT__records__DOT__reader__DOT__state = 9U;
                }
            }
        } else if ((4U & (IData)(vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__state))) {
            if ((2U & (IData)(vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__state))) {
                    if (((IData)(vlSelf->__PVT__splitter__DOT__record_req) 
                         & ((IData)(vlSelf->__VdfgTmp_hed1c005a__0) 
                            & (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__raw_specials__tbl_req_ready)))) {
                        __Vdly__splitter__DOT__records__DOT__reader__DOT__state = 8U;
                    }
                } else if ((IData)(((0U != vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__request_address[2U]) 
                                    | VL_GTE_W(3, vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__request_address, vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__table_end)))) {
                    vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__failed = 1U;
                    vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__code = 0x11U;
                    __Vdly__splitter__DOT__records__DOT__reader__DOT__state = 0xaU;
                } else {
                    __Vdly__splitter__DOT__records__DOT__reader__DOT__state = 7U;
                }
            } else if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__state))) {
                VL_ADD_W(3, __Vtemp_6, vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__data_start, vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__offset_value);
                vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__request_address[0U] 
                    = __Vtemp_6[0U];
                vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__request_address[1U] 
                    = __Vtemp_6[1U];
                vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__request_address[2U] 
                    = (3U & __Vtemp_6[2U]);
                __Vdly__splitter__DOT__records__DOT__reader__DOT__state = 6U;
            } else if ((IData)(((((0ULL != (3ULL & vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__base)) 
                                  | (0U != vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__data_start[2U])) 
                                 | (0U != vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__table_end[2U])) 
                                | ((0U == vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__count) 
                                   | (vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__index 
                                      >= vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__count))))) {
                vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__failed = 1U;
                vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__code = 0x11U;
                __Vdly__splitter__DOT__records__DOT__reader__DOT__state = 0xaU;
            } else {
                __Vdly__splitter__DOT__records__DOT__reader__DOT__state = 5U;
            }
        } else if ((2U & (IData)(vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__state))) {
            if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__state))) {
                __Vtemp_8[0U] = vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__count;
                __Vtemp_8[1U] = 0U;
                __Vtemp_8[2U] = 0U;
                VL_SHIFTL_WWI(66,66,32, __Vtemp_9, __Vtemp_8, 4U);
                VL_ADD_W(3, __Vtemp_10, vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__data_start, __Vtemp_9);
                vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__table_end[0U] 
                    = __Vtemp_10[0U];
                vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__table_end[1U] 
                    = __Vtemp_10[1U];
                vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__table_end[2U] 
                    = (3U & __Vtemp_10[2U]);
                __Vdly__splitter__DOT__records__DOT__reader__DOT__state = 4U;
            } else {
                __Vtemp_12[0U] = 0x20U;
                __Vtemp_12[1U] = 0U;
                __Vtemp_12[2U] = 0U;
                __Vtemp_13[0U] = (IData)(vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__base);
                __Vtemp_13[1U] = (IData)((vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__base 
                                          >> 0x20U));
                __Vtemp_13[2U] = 0U;
                VL_ADD_W(3, __Vtemp_14, __Vtemp_12, __Vtemp_13);
                vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__data_start[0U] 
                    = __Vtemp_14[0U];
                vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__data_start[1U] 
                    = __Vtemp_14[1U];
                vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__data_start[2U] 
                    = (3U & __Vtemp_14[2U]);
                __Vdly__splitter__DOT__records__DOT__reader__DOT__state = 3U;
            }
        } else if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__state))) {
            __Vtemp_16[0U] = vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__index;
            __Vtemp_16[1U] = 0U;
            __Vtemp_16[2U] = 0U;
            VL_SHIFTL_WWI(66,66,32, __Vtemp_17, __Vtemp_16, 4U);
            __Vdly__splitter__DOT__records__DOT__reader__DOT__offset_value[0U] 
                = __Vtemp_17[0U];
            __Vdly__splitter__DOT__records__DOT__reader__DOT__offset_value[1U] 
                = __Vtemp_17[1U];
            __Vdly__splitter__DOT__records__DOT__reader__DOT__offset_value[2U] 
                = (3U & __Vtemp_17[2U]);
            __Vdly__splitter__DOT__records__DOT__reader__DOT__state = 2U;
        } else if ((((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                     & ((8U == (IData)(vlSelf->__PVT__splitter__DOT__state)) 
                        | (0xbU == (IData)(vlSelf->__PVT__splitter__DOT__state)))) 
                    & (IData)(vlSelf->__PVT__splitter__DOT__record_ready))) {
            vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__word_index = 0U;
            if (vlSelf->__PVT__splitter__DOT__special_selected) {
                vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__base 
                    = (((QData)((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__table_bases[0x15U])) 
                        << 0x20U) | (QData)((IData)(
                                                    vlSymsp->TOP.bench__DOT__dut__DOT__table_bases[0x14U])));
                vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__count 
                    = vlSymsp->TOP.bench__DOT__dut__DOT__committed_counts[0xaU];
                vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__index 
                    = vlSelf->__PVT__splitter__DOT__terminal_index;
            } else {
                vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__base 
                    = (((QData)((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__table_bases[0xbU])) 
                        << 0x20U) | (QData)((IData)(
                                                    vlSymsp->TOP.bench__DOT__dut__DOT__table_bases[0xaU])));
                vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__count 
                    = vlSymsp->TOP.bench__DOT__dut__DOT__committed_counts[5U];
                vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__index 
                    = vlSelf->__PVT__splitter__DOT__node_index;
            }
            vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__result_data[0U] = 0U;
            vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__result_data[1U] = 0U;
            vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__result_data[2U] = 0U;
            vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__result_data[3U] = 0U;
            vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__failed = 0U;
            vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__code = 0U;
            __Vdly__splitter__DOT__records__DOT__reader__DOT__state = 1U;
        }
        if (((IData)(vlSelf->__PVT__busy) & ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                                             & (4U 
                                                == (IData)(vlSelf->__PVT__splitter__DOT__encoder__DOT__state))))) {
            vlSelf->__PVT__splitter__DOT__code = ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n)
                                                   ? (IData)(vlSelf->__PVT__splitter__DOT__encoder__DOT__code)
                                                   : 0U);
            __Vdly__splitter__DOT__state = 0x19U;
        } else if ((0x20U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
            vlSelf->__PVT__splitter__DOT__code = 0x12U;
            __Vdly__splitter__DOT__state = 0x19U;
        } else if ((0x10U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
            if ((8U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                if ((4U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                    vlSelf->__PVT__splitter__DOT__code = 0x12U;
                    __Vdly__splitter__DOT__state = 0x19U;
                } else if ((2U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                    if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                        vlSelf->__PVT__splitter__DOT__code = 0x12U;
                        __Vdly__splitter__DOT__state = 0x19U;
                    } else {
                        vlSelf->__PVT__splitter__DOT__output_value 
                            = vlSelf->__PVT__splitter__DOT__plan_value
                            [(0xfU & vlSelf->__PVT__splitter__DOT__output_index)];
                        vlSelf->__PVT__splitter__DOT__output_special 
                            = vlSelf->__PVT__splitter__DOT__plan_special
                            [(0xfU & vlSelf->__PVT__splitter__DOT__output_index)];
                        __Vdly__splitter__DOT__output_last 
                            = (((IData)(1U) + vlSelf->__PVT__splitter__DOT__output_index) 
                               == vlSelf->__PVT__splitter__DOT__plan_count);
                        vlSelf->__PVT__splitter__DOT__output_boundary 
                            = ((~ vlSelf->__PVT__splitter__DOT__plan_special
                                [(0xfU & vlSelf->__PVT__splitter__DOT__output_index)]) 
                               & ((((IData)(1U) + vlSelf->__PVT__splitter__DOT__output_index) 
                                   == vlSelf->__PVT__splitter__DOT__plan_count) 
                                  | vlSelf->__PVT__splitter__DOT__plan_special
                                  [(0xfU & ((IData)(1U) 
                                            + vlSelf->__PVT__splitter__DOT__output_index))]));
                        __Vdly__splitter__DOT__state = 0x17U;
                    }
                } else if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                    __Vdly__splitter__DOT__state = 0x19U;
                } else if (((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                            & (3U == (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__state)))) {
                    if ((1U & (((~ (IData)(vlSymsp->TOP.bench__DOT__boot_done)) 
                                | (2U < vlSymsp->TOP.bench__DOT__dut__DOT__committed_metadata[4U])) 
                               | (vlSymsp->TOP.bench__DOT__dut__DOT__committed_metadata[0xdU] 
                                  >= vlSymsp->TOP.bench__DOT__dut__DOT__committed_counts[5U])))) {
                        vlSelf->__PVT__splitter__DOT__code = 6U;
                        __Vdly__splitter__DOT__state = 0x19U;
                    } else {
                        __Vdly__splitter__DOT__scalar_count = 0U;
                        __Vdly__splitter__DOT__scalar_index = 0U;
                        __Vdly__splitter__DOT__byte_count = 0U;
                        __Vdly__splitter__DOT__scan_index = 0U;
                        __Vdly__splitter__DOT__plan_count = 0U;
                        __Vdly__splitter__DOT__output_index = 0U;
                        vlSelf->__PVT__splitter__DOT__phase = 0U;
                        vlSelf->__PVT__splitter__DOT__code = 0U;
                        __Vdly__splitter__DOT__state = 1U;
                    }
                }
            } else if ((4U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                if ((2U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                    if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                        if (((IData)(vlSelf->out_valid) 
                             & ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                                & (((5U == (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__state)) 
                                    & (IData)(vlSelf->out_special)) 
                                   | ((7U == (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__state)) 
                                      & (IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalization.in_ready)))))) {
                            if (vlSelf->__PVT__splitter__DOT__output_last) {
                                __Vdly__splitter__DOT__state = 0x18U;
                            } else {
                                __Vdly__splitter__DOT__output_index 
                                    = ((IData)(1U) 
                                       + vlSelf->__PVT__splitter__DOT__output_index);
                                __Vdly__splitter__DOT__state = 0x1aU;
                            }
                        }
                    } else if ((0x10U <= vlSelf->__PVT__splitter__DOT__plan_count)) {
                        vlSelf->__PVT__splitter__DOT__code = 0x30U;
                        __Vdly__splitter__DOT__state = 0x19U;
                    } else {
                        __Vdlyvval__splitter__DOT__plan_value__v0 
                            = vlSelf->__PVT__splitter__DOT__scalars
                            [(0xfU & vlSelf->__PVT__splitter__DOT__scan_index)];
                        __Vdlyvset__splitter__DOT__plan_value__v0 = 1U;
                        __Vdlyvdim0__splitter__DOT__plan_value__v0 
                            = (0xfU & vlSelf->__PVT__splitter__DOT__plan_count);
                        __Vdly__splitter__DOT__state = 7U;
                        __Vdlyvset__splitter__DOT__plan_special__v0 = 1U;
                        __Vdlyvdim0__splitter__DOT__plan_special__v0 
                            = (0xfU & vlSelf->__PVT__splitter__DOT__plan_count);
                        __Vdlyvval__splitter__DOT__plan_space__v0 
                            = (1U & (vlSelf->__PVT__splitter__DOT__properties
                                     [(0xfU & vlSelf->__PVT__splitter__DOT__scan_index)] 
                                     >> 8U));
                        __Vdlyvdim0__splitter__DOT__plan_space__v0 
                            = (0xfU & vlSelf->__PVT__splitter__DOT__plan_count);
                        __Vdly__splitter__DOT__plan_count 
                            = ((IData)(1U) + vlSelf->__PVT__splitter__DOT__plan_count);
                        __Vdly__splitter__DOT__scan_index 
                            = ((IData)(1U) + vlSelf->__PVT__splitter__DOT__scan_index);
                    }
                } else if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                    if ((((vlSelf->__PVT__splitter__DOT__best_flags 
                           >> 2U) & (vlSelf->__PVT__splitter__DOT__scan_index 
                                     < vlSelf->__PVT__splitter__DOT__scalar_count)) 
                         & (vlSelf->__PVT__splitter__DOT__properties
                            [(0xfU & vlSelf->__PVT__splitter__DOT__scan_index)] 
                            >> 8U))) {
                        __Vdly__splitter__DOT__scan_index 
                            = ((IData)(1U) + vlSelf->__PVT__splitter__DOT__scan_index);
                    } else {
                        __Vdly__splitter__DOT__state = 7U;
                    }
                } else if ((0x10U <= vlSelf->__PVT__splitter__DOT__plan_count)) {
                    vlSelf->__PVT__splitter__DOT__code = 0x30U;
                    __Vdly__splitter__DOT__state = 0x19U;
                } else {
                    __Vdlyvval__splitter__DOT__plan_value__v1 
                        = vlSelf->__PVT__splitter__DOT__best_token;
                    __Vdlyvset__splitter__DOT__plan_value__v1 = 1U;
                    __Vdlyvdim0__splitter__DOT__plan_value__v1 
                        = (0xfU & vlSelf->__PVT__splitter__DOT__plan_count);
                    __Vdly__splitter__DOT__scan_index 
                        = vlSelf->__PVT__splitter__DOT__best_end;
                    __Vdly__splitter__DOT__state = 0x15U;
                    __Vdlyvset__splitter__DOT__plan_special__v1 = 1U;
                    __Vdlyvdim0__splitter__DOT__plan_special__v1 
                        = (0xfU & vlSelf->__PVT__splitter__DOT__plan_count);
                    __Vdlyvdim0__splitter__DOT__plan_space__v1 
                        = (0xfU & vlSelf->__PVT__splitter__DOT__plan_count);
                    __Vdly__splitter__DOT__plan_count 
                        = ((IData)(1U) + vlSelf->__PVT__splitter__DOT__plan_count);
                }
            } else if ((2U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                    if (((((vlSelf->__PVT__splitter__DOT__best_flags 
                            >> 1U) & (0U != vlSelf->__PVT__splitter__DOT__plan_count)) 
                          & (~ vlSelf->__PVT__splitter__DOT__plan_special
                             [(0xfU & (vlSelf->__PVT__splitter__DOT__plan_count 
                                       - (IData)(1U)))])) 
                         & vlSelf->__PVT__splitter__DOT__plan_space
                         [(0xfU & (vlSelf->__PVT__splitter__DOT__plan_count 
                                   - (IData)(1U)))])) {
                        __Vdly__splitter__DOT__plan_count 
                            = (vlSelf->__PVT__splitter__DOT__plan_count 
                               - (IData)(1U));
                    } else {
                        __Vdly__splitter__DOT__state = 0x14U;
                    }
                } else if (vlSelf->__PVT__splitter__DOT__best_valid) {
                    if ((2U == vlSymsp->TOP.bench__DOT__dut__DOT__committed_metadata[4U])) {
                        vlSelf->__PVT__splitter__DOT__code = 0x13U;
                        __Vdly__splitter__DOT__state = 0x19U;
                    } else {
                        __Vdly__splitter__DOT__state = 0x13U;
                    }
                } else {
                    __Vdly__splitter__DOT__state = 0x16U;
                }
            } else if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                if (((0xffU < (IData)(vlSelf->__PVT__splitter__DOT__edge_record)) 
                     | ((IData)((vlSelf->__PVT__splitter__DOT__edge_record 
                                 >> 0x20U)) >= vlSymsp->TOP.bench__DOT__dut__DOT__committed_counts[5U]))) {
                    vlSelf->__PVT__splitter__DOT__code = 0x12U;
                    __Vdly__splitter__DOT__state = 0x19U;
                } else if (((0xffU & (IData)(vlSelf->__PVT__splitter__DOT__edge_record)) 
                            == vlSelf->__PVT__splitter__DOT__bytes_memory
                            [(0xfU & vlSelf->__PVT__splitter__DOT__cursor)])) {
                    __Vdly__splitter__DOT__cursor = 
                        ((IData)(1U) + vlSelf->__PVT__splitter__DOT__cursor);
                    vlSelf->__PVT__splitter__DOT__node_index 
                        = (IData)((vlSelf->__PVT__splitter__DOT__edge_record 
                                   >> 0x20U));
                    __Vdly__splitter__DOT__state = 8U;
                } else if (((0xffU & (IData)(vlSelf->__PVT__splitter__DOT__edge_record)) 
                            > vlSelf->__PVT__splitter__DOT__bytes_memory
                            [(0xfU & vlSelf->__PVT__splitter__DOT__cursor)])) {
                    __Vdly__splitter__DOT__state = 0x12U;
                } else {
                    __Vdly__splitter__DOT__edge_cursor 
                        = ((IData)(1U) + vlSelf->__PVT__splitter__DOT__edge_cursor);
                    __Vdly__splitter__DOT__state = 0xeU;
                }
            } else if (vlSelf->__PVT__splitter__DOT__edge_valid) {
                if (((IData)(vlSelf->__PVT__splitter__DOT__edge_valid) 
                     & (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__failed))) {
                    vlSelf->__PVT__splitter__DOT__code 
                        = ((IData)(vlSelf->__PVT__splitter__DOT__edge_valid)
                            ? (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__code)
                            : 0U);
                    __Vdly__splitter__DOT__state = 0x19U;
                } else {
                    vlSelf->__PVT__splitter__DOT__edge_record 
                        = (((~ (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__failed)) 
                            & (IData)(vlSelf->__PVT__splitter__DOT__edge_valid))
                            ? vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__result_data
                            : 0ULL);
                    __Vdly__splitter__DOT__state = 0x11U;
                }
            }
        } else if ((8U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
            if ((4U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                if ((2U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                    if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                        if (vlSelf->__PVT__splitter__DOT__edge_ready) {
                            __Vdly__splitter__DOT__state = 0x10U;
                        }
                    } else if ((vlSelf->__PVT__splitter__DOT__edge_end 
                                > (QData)((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__committed_counts[6U])))) {
                        vlSelf->__PVT__splitter__DOT__code = 0x12U;
                        __Vdly__splitter__DOT__state = 0x19U;
                    } else {
                        __Vdly__splitter__DOT__state 
                            = (((vlSelf->__PVT__splitter__DOT__cursor 
                                 == vlSelf->__PVT__splitter__DOT__byte_count) 
                                | (vlSelf->__PVT__splitter__DOT__edge_cursor 
                                   == vlSelf->__PVT__splitter__DOT__edge_count))
                                ? 0x12U : 0xfU);
                    }
                } else if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                    if ((((0ULL != (((QData)((IData)(
                                                     vlSelf->__PVT__splitter__DOT__special_record[3U])) 
                                     << 0x20U) | (QData)((IData)(
                                                                 vlSelf->__PVT__splitter__DOT__special_record[2U])))) 
                          | (0U != (vlSelf->__PVT__splitter__DOT__special_flags 
                                    >> 5U))) | (vlSelf->__PVT__splitter__DOT__special_record[0U] 
                                                >= 
                                                vlSymsp->TOP.bench__DOT__dut__DOT__committed_metadata[2U]))) {
                        vlSelf->__PVT__splitter__DOT__code = 0x12U;
                        __Vdly__splitter__DOT__state = 0x19U;
                    } else {
                        if (((IData)(vlSelf->__PVT__splitter__DOT__eligible) 
                             & (((~ (IData)(vlSelf->__PVT__splitter__DOT__best_valid)) 
                                 | (vlSelf->__PVT__splitter__DOT__terminal_end 
                                    > vlSelf->__PVT__splitter__DOT__best_end)) 
                                | ((vlSelf->__PVT__splitter__DOT__terminal_end 
                                    == vlSelf->__PVT__splitter__DOT__best_end) 
                                   & (vlSelf->__PVT__splitter__DOT__terminal_index 
                                      < vlSelf->__PVT__splitter__DOT__best_record))))) {
                            vlSelf->__PVT__splitter__DOT__best_valid = 1U;
                            vlSelf->__PVT__splitter__DOT__best_end 
                                = vlSelf->__PVT__splitter__DOT__terminal_end;
                            vlSelf->__PVT__splitter__DOT__best_token 
                                = vlSelf->__PVT__splitter__DOT__special_record[0U];
                            vlSelf->__PVT__splitter__DOT__best_flags 
                                = vlSelf->__PVT__splitter__DOT__special_flags;
                            vlSelf->__PVT__splitter__DOT__best_record 
                                = vlSelf->__PVT__splitter__DOT__terminal_index;
                        }
                        __Vdly__splitter__DOT__state = 0xeU;
                    }
                } else if (vlSelf->__PVT__splitter__DOT__record_valid) {
                    if (vlSelf->__PVT__splitter__DOT__record_error) {
                        vlSelf->__PVT__splitter__DOT__code 
                            = vlSelf->__PVT__splitter__DOT__record_code;
                        __Vdly__splitter__DOT__state = 0x19U;
                    } else {
                        vlSelf->__PVT__splitter__DOT__special_record[0U] 
                            = vlSelf->__PVT__splitter__DOT__record_data[0U];
                        vlSelf->__PVT__splitter__DOT__special_record[1U] 
                            = vlSelf->__PVT__splitter__DOT__record_data[1U];
                        vlSelf->__PVT__splitter__DOT__special_record[2U] 
                            = vlSelf->__PVT__splitter__DOT__record_data[2U];
                        vlSelf->__PVT__splitter__DOT__special_record[3U] 
                            = vlSelf->__PVT__splitter__DOT__record_data[3U];
                        __Vdly__splitter__DOT__state = 0xdU;
                    }
                }
            } else if ((2U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                    if (vlSelf->__PVT__splitter__DOT__record_ready) {
                        __Vdly__splitter__DOT__state = 0xcU;
                    }
                } else {
                    __Vdly__splitter__DOT__edge_cursor = 0U;
                    __Vdly__splitter__DOT__edge_first 
                        = vlSelf->__PVT__splitter__DOT__node_record[0U];
                    vlSelf->__PVT__splitter__DOT__edge_count 
                        = vlSelf->__PVT__splitter__DOT__node_record[1U];
                    vlSelf->__PVT__splitter__DOT__terminal_index 
                        = vlSelf->__PVT__splitter__DOT__node_record[2U];
                    if ((0U != vlSelf->__PVT__splitter__DOT__node_record[3U])) {
                        vlSelf->__PVT__splitter__DOT__code = 0x12U;
                        __Vdly__splitter__DOT__state = 0x19U;
                    } else {
                        __Vdly__splitter__DOT__state 
                            = ((((vlSelf->__PVT__splitter__DOT__cursor 
                                  > vlSelf->__PVT__splitter__DOT__scalar_starts
                                  [(0xfU & vlSelf->__PVT__splitter__DOT__scan_index)]) 
                                 & (0U != vlSelf->__PVT__splitter__DOT__terminal_end)) 
                                & (0xffffffffU != vlSelf->__PVT__splitter__DOT__node_record[2U]))
                                ? 0xbU : 0xeU);
                    }
                }
            } else if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                if (vlSelf->__PVT__splitter__DOT__record_valid) {
                    if (vlSelf->__PVT__splitter__DOT__record_error) {
                        vlSelf->__PVT__splitter__DOT__code 
                            = vlSelf->__PVT__splitter__DOT__record_code;
                        __Vdly__splitter__DOT__state = 0x19U;
                    } else {
                        vlSelf->__PVT__splitter__DOT__node_record[0U] 
                            = vlSelf->__PVT__splitter__DOT__record_data[0U];
                        vlSelf->__PVT__splitter__DOT__node_record[1U] 
                            = vlSelf->__PVT__splitter__DOT__record_data[1U];
                        vlSelf->__PVT__splitter__DOT__node_record[2U] 
                            = vlSelf->__PVT__splitter__DOT__record_data[2U];
                        vlSelf->__PVT__splitter__DOT__node_record[3U] 
                            = vlSelf->__PVT__splitter__DOT__record_data[3U];
                        __Vdly__splitter__DOT__state = 0xaU;
                    }
                }
            } else if (vlSelf->__PVT__splitter__DOT__record_ready) {
                __Vdly__splitter__DOT__state = 9U;
            }
        } else if ((4U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
            if ((2U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                    if ((vlSelf->__PVT__splitter__DOT__scan_index 
                         == vlSelf->__PVT__splitter__DOT__scalar_count)) {
                        __Vdly__splitter__DOT__output_index = 0U;
                        __Vdly__splitter__DOT__state = 0x1aU;
                    } else if ((0U == vlSymsp->TOP.bench__DOT__dut__DOT__committed_metadata[4U])) {
                        __Vdly__splitter__DOT__state = 0x16U;
                    } else {
                        __Vdly__splitter__DOT__cursor 
                            = vlSelf->__PVT__splitter__DOT__scalar_starts
                            [(0xfU & vlSelf->__PVT__splitter__DOT__scan_index)];
                        vlSelf->__PVT__splitter__DOT__node_index 
                            = vlSymsp->TOP.bench__DOT__dut__DOT__committed_metadata[0xdU];
                        vlSelf->__PVT__splitter__DOT__best_valid = 0U;
                        __Vdly__splitter__DOT__state = 8U;
                    }
                } else if (vlSelf->__PVT__splitter__DOT__encoder_valid) {
                    if ((0x10U <= vlSelf->__PVT__splitter__DOT__byte_count)) {
                        vlSelf->__PVT__splitter__DOT__code = 0x30U;
                        __Vdly__splitter__DOT__state = 0x19U;
                    } else {
                        __Vdlyvval__splitter__DOT__bytes_memory__v0 
                            = ((IData)(vlSelf->__PVT__splitter__DOT__encoder_valid)
                                ? (0xffU & vlSelf->__PVT__splitter__DOT__encoder__DOT__encoded)
                                : 0U);
                        __Vdlyvset__splitter__DOT__bytes_memory__v0 = 1U;
                        __Vdlyvdim0__splitter__DOT__bytes_memory__v0 
                            = (0xfU & vlSelf->__PVT__splitter__DOT__byte_count);
                        if ((1U == (IData)(vlSelf->__PVT__splitter__DOT__encoded_remaining))) {
                            __Vdlyvval__splitter__DOT__byte_ends__v0 
                                = ((IData)(1U) + vlSelf->__PVT__splitter__DOT__scalar_index);
                            if ((((IData)(1U) + vlSelf->__PVT__splitter__DOT__scalar_index) 
                                 == vlSelf->__PVT__splitter__DOT__scalar_count)) {
                                __Vdly__splitter__DOT__state = 7U;
                            } else {
                                __Vdly__splitter__DOT__scalar_index 
                                    = ((IData)(1U) 
                                       + vlSelf->__PVT__splitter__DOT__scalar_index);
                                __Vdly__splitter__DOT__state = 5U;
                            }
                        } else {
                            __Vdlyvval__splitter__DOT__byte_ends__v0 = 0U;
                        }
                        __Vdlyvdim0__splitter__DOT__byte_ends__v0 
                            = (0xfU & vlSelf->__PVT__splitter__DOT__byte_count);
                        __Vdly__splitter__DOT__byte_count 
                            = ((IData)(1U) + vlSelf->__PVT__splitter__DOT__byte_count);
                        __Vdly__splitter__DOT__encoded_remaining 
                            = (7U & ((IData)(vlSelf->__PVT__splitter__DOT__encoded_remaining) 
                                     - (IData)(1U)));
                    }
                }
            } else if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                if (vlSelf->__PVT__splitter__DOT__encoder_ready) {
                    __Vdlyvval__splitter__DOT__scalar_starts__v0 
                        = vlSelf->__PVT__splitter__DOT__byte_count;
                    __Vdlyvset__splitter__DOT__scalar_starts__v0 = 1U;
                    __Vdlyvdim0__splitter__DOT__scalar_starts__v0 
                        = (0xfU & vlSelf->__PVT__splitter__DOT__scalar_index);
                    __Vdly__splitter__DOT__state = 6U;
                    __Vdly__splitter__DOT__encoded_remaining 
                        = ((0x80U > vlSelf->__PVT__splitter__DOT__scalars
                            [(0xfU & vlSelf->__PVT__splitter__DOT__scalar_index)])
                            ? 1U : ((0x800U > vlSelf->__PVT__splitter__DOT__scalars
                                     [(0xfU & vlSelf->__PVT__splitter__DOT__scalar_index)])
                                     ? 2U : ((0x10000U 
                                              > vlSelf->__PVT__splitter__DOT__scalars
                                              [(0xfU 
                                                & vlSelf->__PVT__splitter__DOT__scalar_index)])
                                              ? 3U : 4U)));
                }
            } else {
                __Vdly__splitter__DOT__state = 5U;
            }
        } else if ((2U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
            if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                if (vlSelf->__PVT__splitter__DOT__class_valid) {
                    if (((IData)(vlSelf->__PVT__splitter__DOT__class_valid) 
                         & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__failed))) {
                        vlSelf->__PVT__splitter__DOT__code 
                            = ((IData)(vlSelf->__PVT__splitter__DOT__class_valid)
                                ? (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__code)
                                : 0U);
                        __Vdly__splitter__DOT__state = 0x19U;
                    } else {
                        __Vdlyvval__splitter__DOT__properties__v0 
                            = (((~ (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__failed)) 
                                & (IData)(vlSelf->__PVT__splitter__DOT__class_valid))
                                ? (0x3ffU & vlSelf->__PVT__splitter__DOT__classification__DOT__property_value)
                                : 0U);
                        __Vdlyvset__splitter__DOT__properties__v0 = 1U;
                        __Vdlyvdim0__splitter__DOT__properties__v0 
                            = (0xfU & vlSelf->__PVT__splitter__DOT__scalar_index);
                        if ((((IData)(1U) + vlSelf->__PVT__splitter__DOT__scalar_index) 
                             == vlSelf->__PVT__splitter__DOT__scalar_count)) {
                            __Vdly__splitter__DOT__scalar_index = 0U;
                            __Vdly__splitter__DOT__state = 4U;
                        } else {
                            __Vdly__splitter__DOT__scalar_index 
                                = ((IData)(1U) + vlSelf->__PVT__splitter__DOT__scalar_index);
                            __Vdly__splitter__DOT__state = 2U;
                        }
                    }
                }
            } else if (vlSelf->__PVT__splitter__DOT__class_ready) {
                __Vdly__splitter__DOT__state = 3U;
            }
        } else if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
            if ((((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                  & (4U == (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__state))) 
                 & (IData)(vlSelf->in_ready))) {
                if ((0x10U <= vlSelf->__PVT__splitter__DOT__scalar_count)) {
                    vlSelf->__PVT__splitter__DOT__code = 0x30U;
                    __Vdly__splitter__DOT__state = 0x19U;
                } else {
                    __Vdlyvval__splitter__DOT__scalars__v0 
                        = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__scalars
                        [(0xfU & vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__scalar_index)];
                    __Vdlyvset__splitter__DOT__scalars__v0 = 1U;
                    __Vdlyvdim0__splitter__DOT__scalars__v0 
                        = (0xfU & vlSelf->__PVT__splitter__DOT__scalar_count);
                    __Vdly__splitter__DOT__scalar_count 
                        = ((IData)(1U) + vlSelf->__PVT__splitter__DOT__scalar_count);
                    if ((((IData)(1U) + vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__scalar_index) 
                         == vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__scalar_count)) {
                        __Vdly__splitter__DOT__scalar_index = 0U;
                        __Vdly__splitter__DOT__state = 2U;
                    } else if ((0x10U == ((IData)(1U) 
                                          + vlSelf->__PVT__splitter__DOT__scalar_count))) {
                        vlSelf->__PVT__splitter__DOT__code = 0x30U;
                        __Vdly__splitter__DOT__state = 0x19U;
                    }
                }
            }
        } else if (((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                    & (3U == (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__state)))) {
            if ((1U & (((~ (IData)(vlSymsp->TOP.bench__DOT__boot_done)) 
                        | (2U < vlSymsp->TOP.bench__DOT__dut__DOT__committed_metadata[4U])) 
                       | (vlSymsp->TOP.bench__DOT__dut__DOT__committed_metadata[0xdU] 
                          >= vlSymsp->TOP.bench__DOT__dut__DOT__committed_counts[5U])))) {
                vlSelf->__PVT__splitter__DOT__code = 6U;
                __Vdly__splitter__DOT__state = 0x19U;
            } else {
                __Vdly__splitter__DOT__scalar_count = 0U;
                __Vdly__splitter__DOT__scalar_index = 0U;
                __Vdly__splitter__DOT__byte_count = 0U;
                __Vdly__splitter__DOT__scan_index = 0U;
                __Vdly__splitter__DOT__plan_count = 0U;
                __Vdly__splitter__DOT__output_index = 0U;
                vlSelf->__PVT__splitter__DOT__phase = 0U;
                vlSelf->__PVT__splitter__DOT__code = 0U;
                __Vdly__splitter__DOT__state = 1U;
            }
        }
        if ((4U & (IData)(vlSelf->__PVT__splitter__DOT__encoder__DOT__state))) {
            if ((2U & (IData)(vlSelf->__PVT__splitter__DOT__encoder__DOT__state))) {
                vlSelf->__PVT__splitter__DOT__encoder__DOT__code = 0x10U;
                __Vdly__splitter__DOT__encoder__DOT__state = 4U;
            } else if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__encoder__DOT__state))) {
                vlSelf->__PVT__splitter__DOT__encoder__DOT__code = 0x10U;
                __Vdly__splitter__DOT__encoder__DOT__state = 4U;
            } else {
                __Vdly__splitter__DOT__encoder__DOT__state = 4U;
            }
        } else if ((2U & (IData)(vlSelf->__PVT__splitter__DOT__encoder__DOT__state))) {
            if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__encoder__DOT__state))) {
                if (vlSelf->__Vcellinp__splitter__DOT__encoder__start) {
                    __Vdly__splitter__DOT__encoder__DOT__remaining = 0U;
                    __Vdly__splitter__DOT__encoder__DOT__encoded = 0U;
                    __Vdly__splitter__DOT__encoder__DOT__final_scalar = 0U;
                    vlSelf->__PVT__splitter__DOT__encoder__DOT__code = 0U;
                    __Vdly__splitter__DOT__encoder__DOT__state = 1U;
                }
            } else if (((IData)(vlSelf->__PVT__splitter__DOT__encoder_valid) 
                        & ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                           & (6U == (IData)(vlSelf->__PVT__splitter__DOT__state))))) {
                if ((1U == (IData)(vlSelf->__PVT__splitter__DOT__encoder__DOT__remaining))) {
                    __Vdly__splitter__DOT__encoder__DOT__state 
                        = ((IData)(vlSelf->__PVT__splitter__DOT__encoder__DOT__final_scalar)
                            ? 3U : 1U);
                } else {
                    __Vdly__splitter__DOT__encoder__DOT__encoded 
                        = VL_SHIFTR_III(32,32,32, vlSelf->__PVT__splitter__DOT__encoder__DOT__encoded, 8U);
                    __Vdly__splitter__DOT__encoder__DOT__remaining 
                        = (7U & ((IData)(vlSelf->__PVT__splitter__DOT__encoder__DOT__remaining) 
                                 - (IData)(1U)));
                }
            }
        } else if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__encoder__DOT__state))) {
            if ((((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                  & (5U == (IData)(vlSelf->__PVT__splitter__DOT__state))) 
                 & (IData)(vlSelf->__PVT__splitter__DOT__encoder_ready))) {
                if (((0x10ffffU < vlSelf->__Vcellinp__splitter__DOT__classification__in_scalar) 
                     | ((0xd800U <= vlSelf->__Vcellinp__splitter__DOT__classification__in_scalar) 
                        & (0xdfffU >= vlSelf->__Vcellinp__splitter__DOT__classification__in_scalar)))) {
                    vlSelf->__PVT__splitter__DOT__encoder__DOT__code = 0x10U;
                    __Vdly__splitter__DOT__encoder__DOT__state = 4U;
                } else {
                    __Vdly__splitter__DOT__encoder__DOT__final_scalar 
                        = (((IData)(1U) + vlSelf->__PVT__splitter__DOT__scalar_index) 
                           == vlSelf->__PVT__splitter__DOT__scalar_count);
                    __Vdly__splitter__DOT__encoder__DOT__state = 2U;
                    if ((0x80U > vlSelf->__Vcellinp__splitter__DOT__classification__in_scalar)) {
                        __Vdly__splitter__DOT__encoder__DOT__encoded 
                            = (0xffU & vlSelf->__Vcellinp__splitter__DOT__classification__in_scalar);
                        __Vdly__splitter__DOT__encoder__DOT__remaining = 1U;
                    } else if ((0x800U > vlSelf->__Vcellinp__splitter__DOT__classification__in_scalar)) {
                        __Vdly__splitter__DOT__encoder__DOT__encoded 
                            = (0x80c0U | ((0x3f00U 
                                           & (vlSelf->__Vcellinp__splitter__DOT__classification__in_scalar 
                                              << 8U)) 
                                          | (0x1fU 
                                             & (vlSelf->__Vcellinp__splitter__DOT__classification__in_scalar 
                                                >> 6U))));
                        __Vdly__splitter__DOT__encoder__DOT__remaining = 2U;
                    } else if ((0x10000U > vlSelf->__Vcellinp__splitter__DOT__classification__in_scalar)) {
                        __Vdly__splitter__DOT__encoder__DOT__encoded 
                            = (0x8080e0U | ((0x3f0000U 
                                             & (vlSelf->__Vcellinp__splitter__DOT__classification__in_scalar 
                                                << 0x10U)) 
                                            | ((0x3f00U 
                                                & (vlSelf->__Vcellinp__splitter__DOT__classification__in_scalar 
                                                   << 2U)) 
                                               | (0xfU 
                                                  & (vlSelf->__Vcellinp__splitter__DOT__classification__in_scalar 
                                                     >> 0xcU)))));
                        __Vdly__splitter__DOT__encoder__DOT__remaining = 3U;
                    } else {
                        __Vdly__splitter__DOT__encoder__DOT__encoded 
                            = (0x808080f0U | ((0x3f000000U 
                                               & (vlSelf->__Vcellinp__splitter__DOT__classification__in_scalar 
                                                  << 0x18U)) 
                                              | ((0x3f0000U 
                                                  & (vlSelf->__Vcellinp__splitter__DOT__classification__in_scalar 
                                                     << 0xaU)) 
                                                 | ((0x3f00U 
                                                     & (vlSelf->__Vcellinp__splitter__DOT__classification__in_scalar 
                                                        >> 4U)) 
                                                    | (7U 
                                                       & (vlSelf->__Vcellinp__splitter__DOT__classification__in_scalar 
                                                          >> 0x12U))))));
                        __Vdly__splitter__DOT__encoder__DOT__remaining = 4U;
                    }
                }
            }
        } else if (vlSelf->__Vcellinp__splitter__DOT__encoder__start) {
            __Vdly__splitter__DOT__encoder__DOT__remaining = 0U;
            __Vdly__splitter__DOT__encoder__DOT__encoded = 0U;
            __Vdly__splitter__DOT__encoder__DOT__final_scalar = 0U;
            vlSelf->__PVT__splitter__DOT__encoder__DOT__code = 0U;
            __Vdly__splitter__DOT__encoder__DOT__state = 1U;
        }
        if ((8U & (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__state))) {
            if ((4U & (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__state))) {
                vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__failed = 1U;
                vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__code = 0x11U;
                __Vdly__splitter__DOT__edges__DOT__reader__DOT__state = 0xaU;
            } else if ((2U & (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__state))) {
                    vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__failed = 1U;
                    vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__code = 0x11U;
                    __Vdly__splitter__DOT__edges__DOT__reader__DOT__state = 0xaU;
                } else if (((IData)(vlSelf->__PVT__splitter__DOT__edge_valid) 
                            & ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                               & (0x10U == (IData)(vlSelf->__PVT__splitter__DOT__state))))) {
                    __Vdly__splitter__DOT__edges__DOT__reader__DOT__state = 0U;
                }
            } else if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__state))) {
                vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__result_data 
                    = (((~ (0xffffffffULL << (0x3fU 
                                              & VL_SHIFTL_III(6,32,32, (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__word_index), 5U)))) 
                        & vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__result_data) 
                       | ((QData)((IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__read_data)) 
                          << (0x3fU & VL_SHIFTL_III(6,32,32, (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__word_index), 5U))));
                if (vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__word_index) {
                    __Vdly__splitter__DOT__edges__DOT__reader__DOT__state = 0xaU;
                } else {
                    vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__word_index 
                        = (1U & ((IData)(1U) + (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__word_index)));
                    __Vtemp_20[0U] = 4U;
                    __Vtemp_20[1U] = 0U;
                    __Vtemp_20[2U] = 0U;
                    VL_ADD_W(3, __Vtemp_21, __Vtemp_20, vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__offset_value);
                    __Vdly__splitter__DOT__edges__DOT__reader__DOT__offset_value[0U] 
                        = __Vtemp_21[0U];
                    __Vdly__splitter__DOT__edges__DOT__reader__DOT__offset_value[1U] 
                        = __Vtemp_21[1U];
                    __Vdly__splitter__DOT__edges__DOT__reader__DOT__offset_value[2U] 
                        = (3U & __Vtemp_21[2U]);
                    __Vdly__splitter__DOT__edges__DOT__reader__DOT__state = 5U;
                }
            } else if ((((IData)(vlSelf->__PVT__splitter__DOT__edge_selected) 
                         & (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__raw_specials__tbl_rsp_valid)) 
                        & (IData)(vlSelf->__PVT__splitter__DOT__edge_rsp_ready))) {
                if (vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer_rsp_error) {
                    vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__failed = 1U;
                    vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__code = 4U;
                    __Vdly__splitter__DOT__edges__DOT__reader__DOT__state = 0xaU;
                } else {
                    vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__read_data 
                        = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer_rsp_data;
                    __Vdly__splitter__DOT__edges__DOT__reader__DOT__state = 9U;
                }
            }
        } else if ((4U & (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__state))) {
            if ((2U & (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__state))) {
                    if (((IData)(vlSelf->__PVT__splitter__DOT__edge_req) 
                         & ((IData)(vlSelf->__PVT__splitter__DOT__edge_selected) 
                            & (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__raw_specials__tbl_req_ready)))) {
                        __Vdly__splitter__DOT__edges__DOT__reader__DOT__state = 8U;
                    }
                } else if ((IData)(((0U != vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__request_address[2U]) 
                                    | VL_GTE_W(3, vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__request_address, vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__table_end)))) {
                    vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__failed = 1U;
                    vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__code = 0x11U;
                    __Vdly__splitter__DOT__edges__DOT__reader__DOT__state = 0xaU;
                } else {
                    __Vdly__splitter__DOT__edges__DOT__reader__DOT__state = 7U;
                }
            } else if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__state))) {
                VL_ADD_W(3, __Vtemp_23, vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__data_start, vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__offset_value);
                vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__request_address[0U] 
                    = __Vtemp_23[0U];
                vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__request_address[1U] 
                    = __Vtemp_23[1U];
                vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__request_address[2U] 
                    = (3U & __Vtemp_23[2U]);
                __Vdly__splitter__DOT__edges__DOT__reader__DOT__state = 6U;
            } else if ((IData)(((((0ULL != (3ULL & vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__base)) 
                                  | (0U != vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__data_start[2U])) 
                                 | (0U != vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__table_end[2U])) 
                                | ((0U == vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__count) 
                                   | (vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__index 
                                      >= vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__count))))) {
                vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__failed = 1U;
                vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__code = 0x11U;
                __Vdly__splitter__DOT__edges__DOT__reader__DOT__state = 0xaU;
            } else {
                __Vdly__splitter__DOT__edges__DOT__reader__DOT__state = 5U;
            }
        } else if ((2U & (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__state))) {
            if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__state))) {
                __Vtemp_25[0U] = vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__count;
                __Vtemp_25[1U] = 0U;
                __Vtemp_25[2U] = 0U;
                VL_SHIFTL_WWI(66,66,32, __Vtemp_26, __Vtemp_25, 3U);
                VL_ADD_W(3, __Vtemp_27, vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__data_start, __Vtemp_26);
                vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__table_end[0U] 
                    = __Vtemp_27[0U];
                vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__table_end[1U] 
                    = __Vtemp_27[1U];
                vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__table_end[2U] 
                    = (3U & __Vtemp_27[2U]);
                __Vdly__splitter__DOT__edges__DOT__reader__DOT__state = 4U;
            } else {
                __Vtemp_29[0U] = 0x20U;
                __Vtemp_29[1U] = 0U;
                __Vtemp_29[2U] = 0U;
                __Vtemp_30[0U] = (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__base);
                __Vtemp_30[1U] = (IData)((vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__base 
                                          >> 0x20U));
                __Vtemp_30[2U] = 0U;
                VL_ADD_W(3, __Vtemp_31, __Vtemp_29, __Vtemp_30);
                vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__data_start[0U] 
                    = __Vtemp_31[0U];
                vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__data_start[1U] 
                    = __Vtemp_31[1U];
                vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__data_start[2U] 
                    = (3U & __Vtemp_31[2U]);
                __Vdly__splitter__DOT__edges__DOT__reader__DOT__state = 3U;
            }
        } else if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__state))) {
            __Vtemp_33[0U] = vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__index;
            __Vtemp_33[1U] = 0U;
            __Vtemp_33[2U] = 0U;
            VL_SHIFTL_WWI(66,66,32, __Vtemp_34, __Vtemp_33, 3U);
            __Vdly__splitter__DOT__edges__DOT__reader__DOT__offset_value[0U] 
                = __Vtemp_34[0U];
            __Vdly__splitter__DOT__edges__DOT__reader__DOT__offset_value[1U] 
                = __Vtemp_34[1U];
            __Vdly__splitter__DOT__edges__DOT__reader__DOT__offset_value[2U] 
                = (3U & __Vtemp_34[2U]);
            __Vdly__splitter__DOT__edges__DOT__reader__DOT__state = 2U;
        } else if ((((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                     & (0xfU == (IData)(vlSelf->__PVT__splitter__DOT__state))) 
                    & (IData)(vlSelf->__PVT__splitter__DOT__edge_ready))) {
            vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__word_index = 0U;
            vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__base 
                = (((QData)((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__table_bases[0xdU])) 
                    << 0x20U) | (QData)((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__table_bases[0xcU])));
            vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__count 
                = vlSymsp->TOP.bench__DOT__dut__DOT__committed_counts[6U];
            vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__index 
                = (vlSelf->__PVT__splitter__DOT__edge_first 
                   + vlSelf->__PVT__splitter__DOT__edge_cursor);
            vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__result_data = 0ULL;
            vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__failed = 0U;
            vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__code = 0U;
            __Vdly__splitter__DOT__edges__DOT__reader__DOT__state = 1U;
        }
        if ((8U & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__state))) {
            vlSelf->__PVT__splitter__DOT__classification__DOT__failed = 1U;
            vlSelf->__PVT__splitter__DOT__classification__DOT__code = 0x12U;
            __Vdly__splitter__DOT__classification__DOT__state = 6U;
        } else if ((4U & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__state))) {
            if ((2U & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__state))) {
                    vlSelf->__PVT__splitter__DOT__classification__DOT__failed = 1U;
                    vlSelf->__PVT__splitter__DOT__classification__DOT__code = 0x12U;
                    __Vdly__splitter__DOT__classification__DOT__state = 6U;
                } else if (((IData)(vlSelf->__PVT__splitter__DOT__class_valid) 
                            & ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                               & (3U == (IData)(vlSelf->__PVT__splitter__DOT__state))))) {
                    __Vdly__splitter__DOT__classification__DOT__state = 0U;
                }
            } else if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__state))) {
                if ((((((vlSelf->__PVT__splitter__DOT__classification__DOT__first_scalar 
                         > vlSelf->__PVT__splitter__DOT__classification__DOT__last_scalar) 
                        | (0x10ffffU < vlSelf->__PVT__splitter__DOT__classification__DOT__last_scalar)) 
                       | ((0xdfffU >= vlSelf->__PVT__splitter__DOT__classification__DOT__first_scalar) 
                          & (0xd800U <= vlSelf->__PVT__splitter__DOT__classification__DOT__last_scalar))) 
                      | (vlSelf->__PVT__splitter__DOT__classification__DOT__class_value 
                         >= vlSelf->__PVT__splitter__DOT__classification__DOT__class_count)) 
                     | (0U != (vlSelf->__PVT__splitter__DOT__classification__DOT__property_value 
                               >> 0xaU)))) {
                    vlSelf->__PVT__splitter__DOT__classification__DOT__failed = 1U;
                    vlSelf->__PVT__splitter__DOT__classification__DOT__code = 0x12U;
                    __Vdly__splitter__DOT__classification__DOT__state = 6U;
                } else if ((vlSelf->__PVT__splitter__DOT__classification__DOT__scalar 
                            < vlSelf->__PVT__splitter__DOT__classification__DOT__first_scalar)) {
                    __Vdly__splitter__DOT__classification__DOT__high_index 
                        = vlSelf->__PVT__splitter__DOT__classification__DOT__middle;
                    __Vdly__splitter__DOT__classification__DOT__state = 2U;
                } else if ((vlSelf->__PVT__splitter__DOT__classification__DOT__scalar 
                            > vlSelf->__PVT__splitter__DOT__classification__DOT__last_scalar)) {
                    __Vdly__splitter__DOT__classification__DOT__low_index 
                        = ((IData)(1U) + vlSelf->__PVT__splitter__DOT__classification__DOT__middle);
                    __Vdly__splitter__DOT__classification__DOT__state = 2U;
                } else {
                    __Vdly__splitter__DOT__classification__DOT__state = 6U;
                }
            } else if (vlSelf->__PVT__splitter__DOT__classification__DOT__reader_valid) {
                if (((IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__reader_valid) 
                     & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__failed))) {
                    vlSelf->__PVT__splitter__DOT__classification__DOT__failed = 1U;
                    vlSelf->__PVT__splitter__DOT__classification__DOT__code 
                        = ((IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__reader_valid)
                            ? (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__code)
                            : 0U);
                    __Vdly__splitter__DOT__classification__DOT__state = 6U;
                } else {
                    vlSelf->__PVT__splitter__DOT__classification__DOT__first_scalar 
                        = vlSelf->__PVT__splitter__DOT__classification__DOT__reader_data[0U];
                    vlSelf->__PVT__splitter__DOT__classification__DOT__last_scalar 
                        = vlSelf->__PVT__splitter__DOT__classification__DOT__reader_data[1U];
                    vlSelf->__PVT__splitter__DOT__classification__DOT__class_value 
                        = vlSelf->__PVT__splitter__DOT__classification__DOT__reader_data[2U];
                    vlSelf->__PVT__splitter__DOT__classification__DOT__property_value 
                        = vlSelf->__PVT__splitter__DOT__classification__DOT__reader_data[3U];
                    __Vdly__splitter__DOT__classification__DOT__state = 5U;
                }
            }
        } else if ((2U & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__state))) {
            if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__state))) {
                if (vlSelf->__PVT__splitter__DOT__classification__DOT__reader_ready) {
                    __Vdly__splitter__DOT__classification__DOT__state = 4U;
                }
            } else if ((vlSelf->__PVT__splitter__DOT__classification__DOT__low_index 
                        >= vlSelf->__PVT__splitter__DOT__classification__DOT__high_index)) {
                vlSelf->__PVT__splitter__DOT__classification__DOT__failed = 1U;
                vlSelf->__PVT__splitter__DOT__classification__DOT__code = 0x12U;
                __Vdly__splitter__DOT__classification__DOT__state = 6U;
            } else {
                __Vdly__splitter__DOT__classification__DOT__middle 
                    = (vlSelf->__PVT__splitter__DOT__classification__DOT__low_index 
                       + VL_SHIFTR_III(32,32,32, (vlSelf->__PVT__splitter__DOT__classification__DOT__high_index 
                                                  - vlSelf->__PVT__splitter__DOT__classification__DOT__low_index), 1U));
                __Vdly__splitter__DOT__classification__DOT__state = 3U;
            }
        } else if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__state))) {
            if (((0x10ffffU < vlSelf->__PVT__splitter__DOT__classification__DOT__scalar) 
                 | ((0xd800U <= vlSelf->__PVT__splitter__DOT__classification__DOT__scalar) 
                    & (0xdfffU >= vlSelf->__PVT__splitter__DOT__classification__DOT__scalar)))) {
                vlSelf->__PVT__splitter__DOT__classification__DOT__failed = 1U;
                vlSelf->__PVT__splitter__DOT__classification__DOT__code = 0x10U;
                __Vdly__splitter__DOT__classification__DOT__state = 6U;
            } else if ((1U & ((((~ (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__admitted)) 
                                | (0U == vlSelf->__PVT__splitter__DOT__classification__DOT__range_count)) 
                               | (0U == vlSelf->__PVT__splitter__DOT__classification__DOT__class_count)) 
                              | (0U != (3U & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__base)))))) {
                vlSelf->__PVT__splitter__DOT__classification__DOT__failed = 1U;
                vlSelf->__PVT__splitter__DOT__classification__DOT__code = 6U;
                __Vdly__splitter__DOT__classification__DOT__state = 6U;
            } else {
                __Vdly__splitter__DOT__classification__DOT__state = 2U;
            }
        } else if ((((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                     & (2U == (IData)(vlSelf->__PVT__splitter__DOT__state))) 
                    & (IData)(vlSelf->__PVT__splitter__DOT__class_ready))) {
            vlSelf->__PVT__splitter__DOT__classification__DOT__admitted 
                = vlSymsp->TOP.bench__DOT__boot_done;
            __Vdly__splitter__DOT__classification__DOT__base 
                = (((QData)((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__table_bases[0xfU])) 
                    << 0x20U) | (QData)((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__table_bases[0xeU])));
            __Vdly__splitter__DOT__classification__DOT__range_count 
                = vlSymsp->TOP.bench__DOT__dut__DOT__committed_counts[7U];
            vlSelf->__PVT__splitter__DOT__classification__DOT__class_count 
                = vlSymsp->TOP.bench__DOT__dut__DOT__committed_metadata[9U];
            vlSelf->__PVT__splitter__DOT__classification__DOT__scalar 
                = vlSelf->__Vcellinp__splitter__DOT__classification__in_scalar;
            __Vdly__splitter__DOT__classification__DOT__low_index = 0U;
            __Vdly__splitter__DOT__classification__DOT__high_index 
                = vlSymsp->TOP.bench__DOT__dut__DOT__committed_counts[7U];
            vlSelf->__PVT__splitter__DOT__classification__DOT__failed = 0U;
            vlSelf->__PVT__splitter__DOT__classification__DOT__code = 0U;
            vlSelf->__PVT__splitter__DOT__classification__DOT__class_value = 0U;
            vlSelf->__PVT__splitter__DOT__classification__DOT__property_value = 0U;
            __Vdly__splitter__DOT__classification__DOT__state = 1U;
        }
        if ((8U & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
            if ((4U & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
                vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__failed = 1U;
                vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__code = 0x11U;
                __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 0xaU;
            } else if ((2U & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
                    vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__failed = 1U;
                    vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__code = 0x11U;
                    __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 0xaU;
                } else if (((IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__reader_valid) 
                            & ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                               & (4U == (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__state))))) {
                    __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 0U;
                }
            } else if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
                VL_ASSIGNSEL_WI(128,32,(0x7fU & VL_SHIFTL_III(7,32,32, (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__word_index), 5U)), vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data, vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__read_data);
                if ((3U == (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__word_index))) {
                    __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 0xaU;
                } else {
                    vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__word_index 
                        = (3U & ((IData)(1U) + (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__word_index)));
                    __Vtemp_37[0U] = 4U;
                    __Vtemp_37[1U] = 0U;
                    __Vtemp_37[2U] = 0U;
                    VL_ADD_W(3, __Vtemp_38, __Vtemp_37, vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value);
                    __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[0U] 
                        = __Vtemp_38[0U];
                    __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[1U] 
                        = __Vtemp_38[1U];
                    __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[2U] 
                        = (3U & __Vtemp_38[2U]);
                    __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 5U;
                }
            } else if ((((IData)(vlSelf->__PVT__splitter__DOT__classify_selected) 
                         & (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__raw_specials__tbl_rsp_valid)) 
                        & (IData)(vlSelf->__PVT__splitter__DOT__class_rsp_ready))) {
                if (vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer_rsp_error) {
                    vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__failed = 1U;
                    vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__code = 4U;
                    __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 0xaU;
                } else {
                    vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__read_data 
                        = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer_rsp_data;
                    __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 9U;
                }
            }
        } else if ((4U & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
            if ((2U & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
                    if (((IData)(vlSelf->__PVT__splitter__DOT__class_req) 
                         & ((IData)(vlSelf->__PVT__splitter__DOT__classify_selected) 
                            & (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__raw_specials__tbl_req_ready)))) {
                        __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 8U;
                    }
                } else if ((IData)(((0U != vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__request_address[2U]) 
                                    | VL_GTE_W(3, vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__request_address, vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__table_end)))) {
                    vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__failed = 1U;
                    vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__code = 0x11U;
                    __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 0xaU;
                } else {
                    __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 7U;
                }
            } else if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
                VL_ADD_W(3, __Vtemp_40, vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__data_start, vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value);
                vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__request_address[0U] 
                    = __Vtemp_40[0U];
                vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__request_address[1U] 
                    = __Vtemp_40[1U];
                vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__request_address[2U] 
                    = (3U & __Vtemp_40[2U]);
                __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 6U;
            } else if ((IData)(((((0ULL != (3ULL & vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__base)) 
                                  | (0U != vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__data_start[2U])) 
                                 | (0U != vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__table_end[2U])) 
                                | ((0U == vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__count) 
                                   | (vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__index 
                                      >= vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__count))))) {
                vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__failed = 1U;
                vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__code = 0x11U;
                __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 0xaU;
            } else {
                __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 5U;
            }
        } else if ((2U & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
            if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
                __Vtemp_42[0U] = vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__count;
                __Vtemp_42[1U] = 0U;
                __Vtemp_42[2U] = 0U;
                VL_SHIFTL_WWI(66,66,32, __Vtemp_43, __Vtemp_42, 4U);
                VL_ADD_W(3, __Vtemp_44, vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__data_start, __Vtemp_43);
                vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__table_end[0U] 
                    = __Vtemp_44[0U];
                vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__table_end[1U] 
                    = __Vtemp_44[1U];
                vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__table_end[2U] 
                    = (3U & __Vtemp_44[2U]);
                __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 4U;
            } else {
                __Vtemp_46[0U] = 0x20U;
                __Vtemp_46[1U] = 0U;
                __Vtemp_46[2U] = 0U;
                __Vtemp_47[0U] = (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__base);
                __Vtemp_47[1U] = (IData)((vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__base 
                                          >> 0x20U));
                __Vtemp_47[2U] = 0U;
                VL_ADD_W(3, __Vtemp_48, __Vtemp_46, __Vtemp_47);
                vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__data_start[0U] 
                    = __Vtemp_48[0U];
                vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__data_start[1U] 
                    = __Vtemp_48[1U];
                vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__data_start[2U] 
                    = (3U & __Vtemp_48[2U]);
                __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 3U;
            }
        } else if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
            __Vtemp_50[0U] = vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__index;
            __Vtemp_50[1U] = 0U;
            __Vtemp_50[2U] = 0U;
            VL_SHIFTL_WWI(66,66,32, __Vtemp_51, __Vtemp_50, 4U);
            __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[0U] 
                = __Vtemp_51[0U];
            __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[1U] 
                = __Vtemp_51[1U];
            __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[2U] 
                = (3U & __Vtemp_51[2U]);
            __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 2U;
        } else if ((((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                     & (3U == (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__state))) 
                    & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__reader_ready))) {
            vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__word_index = 0U;
            vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__base 
                = vlSelf->__PVT__splitter__DOT__classification__DOT__base;
            vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__count 
                = vlSelf->__PVT__splitter__DOT__classification__DOT__range_count;
            vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__index 
                = vlSelf->__PVT__splitter__DOT__classification__DOT__middle;
            vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[0U] = 0U;
            vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[1U] = 0U;
            vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[2U] = 0U;
            vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[3U] = 0U;
            vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__failed = 0U;
            vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__code = 0U;
            __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 1U;
        }
    } else {
        vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__word_index = 0U;
        __Vdly__splitter__DOT__records__DOT__reader__DOT__offset_value[0U] = 0U;
        __Vdly__splitter__DOT__records__DOT__reader__DOT__offset_value[1U] = 0U;
        __Vdly__splitter__DOT__records__DOT__reader__DOT__offset_value[2U] = 0U;
        __Vdly__splitter__DOT__records__DOT__reader__DOT__state = 0U;
        vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__base = 0ULL;
        vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__count = 0U;
        vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__index = 0U;
        vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__data_start[0U] = 0U;
        vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__data_start[1U] = 0U;
        vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__data_start[2U] = 0U;
        vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__table_end[0U] = 0U;
        vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__table_end[1U] = 0U;
        vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__table_end[2U] = 0U;
        vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__request_address[0U] = 0U;
        vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__request_address[1U] = 0U;
        vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__request_address[2U] = 0U;
        vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__result_data[0U] = 0U;
        vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__result_data[1U] = 0U;
        vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__result_data[2U] = 0U;
        vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__result_data[3U] = 0U;
        vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__read_data = 0U;
        vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__failed = 0U;
        vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__code = 0U;
        __Vdly__splitter__DOT__cursor = 0U;
        __Vdly__splitter__DOT__edge_cursor = 0U;
        __Vdly__splitter__DOT__state = 0U;
        __Vdly__splitter__DOT__scalar_count = 0U;
        __Vdly__splitter__DOT__scalar_index = 0U;
        __Vdly__splitter__DOT__byte_count = 0U;
        __Vdly__splitter__DOT__scan_index = 0U;
        __Vdly__splitter__DOT__plan_count = 0U;
        __Vdly__splitter__DOT__output_index = 0U;
        __Vdly__splitter__DOT__encoded_remaining = 0U;
        vlSelf->__PVT__splitter__DOT__node_index = 0U;
        __Vdly__splitter__DOT__edge_first = 0U;
        vlSelf->__PVT__splitter__DOT__edge_count = 0U;
        vlSelf->__PVT__splitter__DOT__terminal_index = 0U;
        vlSelf->__PVT__splitter__DOT__best_end = 0U;
        vlSelf->__PVT__splitter__DOT__best_token = 0U;
        vlSelf->__PVT__splitter__DOT__best_flags = 0U;
        vlSelf->__PVT__splitter__DOT__best_record = 0U;
        vlSelf->__PVT__splitter__DOT__best_valid = 0U;
        vlSelf->__PVT__splitter__DOT__phase = 0U;
        vlSelf->__PVT__splitter__DOT__node_record[0U] = 0U;
        vlSelf->__PVT__splitter__DOT__node_record[1U] = 0U;
        vlSelf->__PVT__splitter__DOT__node_record[2U] = 0U;
        vlSelf->__PVT__splitter__DOT__node_record[3U] = 0U;
        vlSelf->__PVT__splitter__DOT__special_record[0U] = 0U;
        vlSelf->__PVT__splitter__DOT__special_record[1U] = 0U;
        vlSelf->__PVT__splitter__DOT__special_record[2U] = 0U;
        vlSelf->__PVT__splitter__DOT__special_record[3U] = 0U;
        vlSelf->__PVT__splitter__DOT__edge_record = 0ULL;
        vlSelf->__PVT__splitter__DOT__code = 0U;
        vlSelf->__PVT__splitter__DOT__output_value = 0U;
        vlSelf->__PVT__splitter__DOT__output_special = 0U;
        vlSelf->__PVT__splitter__DOT__output_boundary = 0U;
        __Vdly__splitter__DOT__output_last = 0U;
        __Vdly__splitter__DOT__encoder__DOT__state = 0U;
        __Vdly__splitter__DOT__encoder__DOT__remaining = 0U;
        __Vdly__splitter__DOT__encoder__DOT__encoded = 0U;
        __Vdly__splitter__DOT__encoder__DOT__final_scalar = 0U;
        vlSelf->__PVT__splitter__DOT__encoder__DOT__code = 0U;
        vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__word_index = 0U;
        __Vdly__splitter__DOT__edges__DOT__reader__DOT__offset_value[0U] = 0U;
        __Vdly__splitter__DOT__edges__DOT__reader__DOT__offset_value[1U] = 0U;
        __Vdly__splitter__DOT__edges__DOT__reader__DOT__offset_value[2U] = 0U;
        __Vdly__splitter__DOT__edges__DOT__reader__DOT__state = 0U;
        vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__base = 0ULL;
        vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__count = 0U;
        vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__index = 0U;
        vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__data_start[0U] = 0U;
        vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__data_start[1U] = 0U;
        vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__data_start[2U] = 0U;
        vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__table_end[0U] = 0U;
        vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__table_end[1U] = 0U;
        vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__table_end[2U] = 0U;
        vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__request_address[0U] = 0U;
        vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__request_address[1U] = 0U;
        vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__request_address[2U] = 0U;
        vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__result_data = 0ULL;
        vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__read_data = 0U;
        vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__failed = 0U;
        vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__code = 0U;
        __Vdly__splitter__DOT__classification__DOT__state = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__admitted = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__failed = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__code = 0U;
        __Vdly__splitter__DOT__classification__DOT__base = 0ULL;
        vlSelf->__PVT__splitter__DOT__classification__DOT__scalar = 0U;
        __Vdly__splitter__DOT__classification__DOT__range_count = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__class_count = 0U;
        __Vdly__splitter__DOT__classification__DOT__low_index = 0U;
        __Vdly__splitter__DOT__classification__DOT__high_index = 0U;
        __Vdly__splitter__DOT__classification__DOT__middle = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__first_scalar = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__last_scalar = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__class_value = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__property_value = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__word_index = 0U;
        __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[0U] = 0U;
        __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[1U] = 0U;
        __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[2U] = 0U;
        __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__base = 0ULL;
        vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__count = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__index = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__data_start[0U] = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__data_start[1U] = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__data_start[2U] = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__table_end[0U] = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__table_end[1U] = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__table_end[2U] = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__request_address[0U] = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__request_address[1U] = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__request_address[2U] = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[0U] = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[1U] = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[2U] = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[3U] = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__read_data = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__failed = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__code = 0U;
    }
    vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__offset_value[0U] 
        = __Vdly__splitter__DOT__records__DOT__reader__DOT__offset_value[0U];
    vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__offset_value[1U] 
        = __Vdly__splitter__DOT__records__DOT__reader__DOT__offset_value[1U];
    vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__offset_value[2U] 
        = __Vdly__splitter__DOT__records__DOT__reader__DOT__offset_value[2U];
    vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__state 
        = __Vdly__splitter__DOT__records__DOT__reader__DOT__state;
    vlSelf->__PVT__splitter__DOT__byte_count = __Vdly__splitter__DOT__byte_count;
    vlSelf->__PVT__splitter__DOT__plan_count = __Vdly__splitter__DOT__plan_count;
    vlSelf->__PVT__splitter__DOT__output_index = __Vdly__splitter__DOT__output_index;
    vlSelf->__PVT__splitter__DOT__output_last = __Vdly__splitter__DOT__output_last;
    vlSelf->__PVT__splitter__DOT__encoded_remaining 
        = __Vdly__splitter__DOT__encoded_remaining;
    if (__Vdlyvset__splitter__DOT__scalar_starts__v0) {
        vlSelf->__PVT__splitter__DOT__scalar_starts[__Vdlyvdim0__splitter__DOT__scalar_starts__v0] 
            = __Vdlyvval__splitter__DOT__scalar_starts__v0;
    }
    if (__Vdlyvset__splitter__DOT__plan_value__v0) {
        vlSelf->__PVT__splitter__DOT__plan_value[__Vdlyvdim0__splitter__DOT__plan_value__v0] 
            = __Vdlyvval__splitter__DOT__plan_value__v0;
    }
    if (__Vdlyvset__splitter__DOT__plan_value__v1) {
        vlSelf->__PVT__splitter__DOT__plan_value[__Vdlyvdim0__splitter__DOT__plan_value__v1] 
            = __Vdlyvval__splitter__DOT__plan_value__v1;
    }
    if (__Vdlyvset__splitter__DOT__scalars__v0) {
        vlSelf->__PVT__splitter__DOT__scalars[__Vdlyvdim0__splitter__DOT__scalars__v0] 
            = __Vdlyvval__splitter__DOT__scalars__v0;
    }
    vlSelf->__PVT__splitter__DOT__scan_index = __Vdly__splitter__DOT__scan_index;
    if (__Vdlyvset__splitter__DOT__plan_special__v0) {
        vlSelf->__PVT__splitter__DOT__plan_special[__Vdlyvdim0__splitter__DOT__plan_special__v0] = 0U;
        vlSelf->__PVT__splitter__DOT__plan_space[__Vdlyvdim0__splitter__DOT__plan_space__v0] 
            = __Vdlyvval__splitter__DOT__plan_space__v0;
    }
    if (__Vdlyvset__splitter__DOT__plan_special__v1) {
        vlSelf->__PVT__splitter__DOT__plan_special[__Vdlyvdim0__splitter__DOT__plan_special__v1] = 1U;
        vlSelf->__PVT__splitter__DOT__plan_space[__Vdlyvdim0__splitter__DOT__plan_space__v1] = 0U;
    }
    if (__Vdlyvset__splitter__DOT__properties__v0) {
        vlSelf->__PVT__splitter__DOT__properties[__Vdlyvdim0__splitter__DOT__properties__v0] 
            = __Vdlyvval__splitter__DOT__properties__v0;
    }
    if (__Vdlyvset__splitter__DOT__bytes_memory__v0) {
        vlSelf->__PVT__splitter__DOT__bytes_memory[__Vdlyvdim0__splitter__DOT__bytes_memory__v0] 
            = __Vdlyvval__splitter__DOT__bytes_memory__v0;
        vlSelf->__PVT__splitter__DOT__byte_ends[__Vdlyvdim0__splitter__DOT__byte_ends__v0] 
            = __Vdlyvval__splitter__DOT__byte_ends__v0;
    }
    vlSelf->__PVT__splitter__DOT__cursor = __Vdly__splitter__DOT__cursor;
    vlSelf->__PVT__splitter__DOT__special_flags = vlSelf->__PVT__splitter__DOT__special_record[1U];
    __VdfgTmp_hb6edd8f3__0 = vlSelf->__PVT__splitter__DOT__byte_ends
        [(0xfU & (vlSelf->__PVT__splitter__DOT__cursor 
                  - (IData)(1U)))];
    vlSelf->__PVT__splitter__DOT__terminal_end = ((0U 
                                                   == vlSelf->__PVT__splitter__DOT__cursor)
                                                   ? 0U
                                                   : __VdfgTmp_hb6edd8f3__0);
    vlSelf->__PVT__splitter__DOT__encoder__DOT__remaining 
        = __Vdly__splitter__DOT__encoder__DOT__remaining;
    vlSelf->__PVT__splitter__DOT__encoder__DOT__final_scalar 
        = __Vdly__splitter__DOT__encoder__DOT__final_scalar;
    vlSelf->__PVT__splitter__DOT__encoder__DOT__encoded 
        = __Vdly__splitter__DOT__encoder__DOT__encoded;
    vlSelf->__PVT__splitter__DOT__scalar_index = __Vdly__splitter__DOT__scalar_index;
    vlSelf->__PVT__splitter__DOT__encoder__DOT__state 
        = __Vdly__splitter__DOT__encoder__DOT__state;
    vlSelf->__PVT__splitter__DOT__scalar_count = __Vdly__splitter__DOT__scalar_count;
    vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__offset_value[0U] 
        = __Vdly__splitter__DOT__edges__DOT__reader__DOT__offset_value[0U];
    vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__offset_value[1U] 
        = __Vdly__splitter__DOT__edges__DOT__reader__DOT__offset_value[1U];
    vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__offset_value[2U] 
        = __Vdly__splitter__DOT__edges__DOT__reader__DOT__offset_value[2U];
    vlSelf->__PVT__splitter__DOT__edge_cursor = __Vdly__splitter__DOT__edge_cursor;
    vlSelf->__PVT__splitter__DOT__edge_first = __Vdly__splitter__DOT__edge_first;
    vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__state 
        = __Vdly__splitter__DOT__edges__DOT__reader__DOT__state;
    vlSelf->__PVT__splitter__DOT__classification__DOT__high_index 
        = __Vdly__splitter__DOT__classification__DOT__high_index;
    vlSelf->__PVT__splitter__DOT__classification__DOT__low_index 
        = __Vdly__splitter__DOT__classification__DOT__low_index;
    vlSelf->__PVT__splitter__DOT__state = __Vdly__splitter__DOT__state;
    vlSelf->__Vcellinp__splitter__DOT__classification__in_scalar 
        = vlSelf->__PVT__splitter__DOT__scalars[(0xfU 
                                                 & vlSelf->__PVT__splitter__DOT__scalar_index)];
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
    vlSelf->__PVT__splitter__DOT__edge_end = (0x1ffffffffULL 
                                              & ((QData)((IData)(vlSelf->__PVT__splitter__DOT__edge_first)) 
                                                 + (QData)((IData)(vlSelf->__PVT__splitter__DOT__edge_count))));
    vlSelf->__PVT__splitter__DOT__special_selected 
        = ((0xbU == (IData)(vlSelf->__PVT__splitter__DOT__state)) 
           | (0xcU == (IData)(vlSelf->__PVT__splitter__DOT__state)));
    vlSelf->__PVT__splitter__DOT__edge_selected = (
                                                   (0xfU 
                                                    == (IData)(vlSelf->__PVT__splitter__DOT__state)) 
                                                   | (0x10U 
                                                      == (IData)(vlSelf->__PVT__splitter__DOT__state)));
    vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[0U] 
        = __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[0U];
    vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[1U] 
        = __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[1U];
    vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[2U] 
        = __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[2U];
    vlSelf->__PVT__splitter__DOT__classification__DOT__base 
        = __Vdly__splitter__DOT__classification__DOT__base;
    vlSelf->__PVT__splitter__DOT__classification__DOT__range_count 
        = __Vdly__splitter__DOT__classification__DOT__range_count;
    vlSelf->__PVT__splitter__DOT__classification__DOT__middle 
        = __Vdly__splitter__DOT__classification__DOT__middle;
    vlSelf->__PVT__splitter__DOT__classification__DOT__state 
        = __Vdly__splitter__DOT__classification__DOT__state;
    vlSelf->__PVT__splitter__DOT__classify_selected 
        = ((2U == (IData)(vlSelf->__PVT__splitter__DOT__state)) 
           | (3U == (IData)(vlSelf->__PVT__splitter__DOT__state)));
    vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state 
        = __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state;
    vlSelf->__VdfgTmp_hed1c005a__0 = (1U & ((~ (IData)(vlSelf->__PVT__splitter__DOT__classify_selected)) 
                                            & (~ (IData)(vlSelf->__PVT__splitter__DOT__edge_selected))));
}

VL_INLINE_OPT void Vbench_anvil_edge_special_splitter__pi7___act_comb__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalized_specials__0(Vbench_anvil_edge_special_splitter__pi7* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+            Vbench_anvil_edge_special_splitter__pi7___act_comb__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalized_specials__0\n"); );
    // Body
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
}

VL_INLINE_OPT void Vbench_anvil_edge_special_splitter__pi7___nba_sequent__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalized_specials__0(Vbench_anvil_edge_special_splitter__pi7* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+            Vbench_anvil_edge_special_splitter__pi7___nba_sequent__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalized_specials__0\n"); );
    // Init
    IData/*31:0*/ __VdfgTmp_hb6edd8f3__0;
    __VdfgTmp_hb6edd8f3__0 = 0;
    CData/*5:0*/ __Vdly__splitter__DOT__state;
    __Vdly__splitter__DOT__state = 0;
    CData/*0:0*/ __Vdly__splitter__DOT__output_last;
    __Vdly__splitter__DOT__output_last = 0;
    IData/*31:0*/ __Vdly__splitter__DOT__scalar_count;
    __Vdly__splitter__DOT__scalar_count = 0;
    IData/*31:0*/ __Vdly__splitter__DOT__scalar_index;
    __Vdly__splitter__DOT__scalar_index = 0;
    IData/*31:0*/ __Vdly__splitter__DOT__byte_count;
    __Vdly__splitter__DOT__byte_count = 0;
    IData/*31:0*/ __Vdly__splitter__DOT__scan_index;
    __Vdly__splitter__DOT__scan_index = 0;
    IData/*31:0*/ __Vdly__splitter__DOT__plan_count;
    __Vdly__splitter__DOT__plan_count = 0;
    IData/*31:0*/ __Vdly__splitter__DOT__output_index;
    __Vdly__splitter__DOT__output_index = 0;
    CData/*3:0*/ __Vdlyvdim0__splitter__DOT__plan_value__v0;
    __Vdlyvdim0__splitter__DOT__plan_value__v0 = 0;
    IData/*31:0*/ __Vdlyvval__splitter__DOT__plan_value__v0;
    __Vdlyvval__splitter__DOT__plan_value__v0 = 0;
    CData/*0:0*/ __Vdlyvset__splitter__DOT__plan_value__v0;
    __Vdlyvset__splitter__DOT__plan_value__v0 = 0;
    CData/*3:0*/ __Vdlyvdim0__splitter__DOT__plan_special__v0;
    __Vdlyvdim0__splitter__DOT__plan_special__v0 = 0;
    CData/*0:0*/ __Vdlyvset__splitter__DOT__plan_special__v0;
    __Vdlyvset__splitter__DOT__plan_special__v0 = 0;
    CData/*3:0*/ __Vdlyvdim0__splitter__DOT__plan_space__v0;
    __Vdlyvdim0__splitter__DOT__plan_space__v0 = 0;
    CData/*0:0*/ __Vdlyvval__splitter__DOT__plan_space__v0;
    __Vdlyvval__splitter__DOT__plan_space__v0 = 0;
    CData/*3:0*/ __Vdlyvdim0__splitter__DOT__plan_value__v1;
    __Vdlyvdim0__splitter__DOT__plan_value__v1 = 0;
    IData/*31:0*/ __Vdlyvval__splitter__DOT__plan_value__v1;
    __Vdlyvval__splitter__DOT__plan_value__v1 = 0;
    CData/*0:0*/ __Vdlyvset__splitter__DOT__plan_value__v1;
    __Vdlyvset__splitter__DOT__plan_value__v1 = 0;
    CData/*3:0*/ __Vdlyvdim0__splitter__DOT__plan_special__v1;
    __Vdlyvdim0__splitter__DOT__plan_special__v1 = 0;
    CData/*0:0*/ __Vdlyvset__splitter__DOT__plan_special__v1;
    __Vdlyvset__splitter__DOT__plan_special__v1 = 0;
    CData/*3:0*/ __Vdlyvdim0__splitter__DOT__plan_space__v1;
    __Vdlyvdim0__splitter__DOT__plan_space__v1 = 0;
    IData/*31:0*/ __Vdly__splitter__DOT__cursor;
    __Vdly__splitter__DOT__cursor = 0;
    IData/*31:0*/ __Vdly__splitter__DOT__edge_cursor;
    __Vdly__splitter__DOT__edge_cursor = 0;
    IData/*31:0*/ __Vdly__splitter__DOT__edge_first;
    __Vdly__splitter__DOT__edge_first = 0;
    CData/*3:0*/ __Vdlyvdim0__splitter__DOT__bytes_memory__v0;
    __Vdlyvdim0__splitter__DOT__bytes_memory__v0 = 0;
    CData/*7:0*/ __Vdlyvval__splitter__DOT__bytes_memory__v0;
    __Vdlyvval__splitter__DOT__bytes_memory__v0 = 0;
    CData/*0:0*/ __Vdlyvset__splitter__DOT__bytes_memory__v0;
    __Vdlyvset__splitter__DOT__bytes_memory__v0 = 0;
    CData/*3:0*/ __Vdlyvdim0__splitter__DOT__byte_ends__v0;
    __Vdlyvdim0__splitter__DOT__byte_ends__v0 = 0;
    IData/*31:0*/ __Vdlyvval__splitter__DOT__byte_ends__v0;
    __Vdlyvval__splitter__DOT__byte_ends__v0 = 0;
    CData/*2:0*/ __Vdly__splitter__DOT__encoded_remaining;
    __Vdly__splitter__DOT__encoded_remaining = 0;
    CData/*3:0*/ __Vdlyvdim0__splitter__DOT__scalar_starts__v0;
    __Vdlyvdim0__splitter__DOT__scalar_starts__v0 = 0;
    IData/*31:0*/ __Vdlyvval__splitter__DOT__scalar_starts__v0;
    __Vdlyvval__splitter__DOT__scalar_starts__v0 = 0;
    CData/*0:0*/ __Vdlyvset__splitter__DOT__scalar_starts__v0;
    __Vdlyvset__splitter__DOT__scalar_starts__v0 = 0;
    CData/*3:0*/ __Vdlyvdim0__splitter__DOT__properties__v0;
    __Vdlyvdim0__splitter__DOT__properties__v0 = 0;
    SData/*9:0*/ __Vdlyvval__splitter__DOT__properties__v0;
    __Vdlyvval__splitter__DOT__properties__v0 = 0;
    CData/*0:0*/ __Vdlyvset__splitter__DOT__properties__v0;
    __Vdlyvset__splitter__DOT__properties__v0 = 0;
    CData/*3:0*/ __Vdlyvdim0__splitter__DOT__scalars__v0;
    __Vdlyvdim0__splitter__DOT__scalars__v0 = 0;
    IData/*31:0*/ __Vdlyvval__splitter__DOT__scalars__v0;
    __Vdlyvval__splitter__DOT__scalars__v0 = 0;
    CData/*0:0*/ __Vdlyvset__splitter__DOT__scalars__v0;
    __Vdlyvset__splitter__DOT__scalars__v0 = 0;
    CData/*3:0*/ __Vdly__splitter__DOT__classification__DOT__state;
    __Vdly__splitter__DOT__classification__DOT__state = 0;
    IData/*31:0*/ __Vdly__splitter__DOT__classification__DOT__high_index;
    __Vdly__splitter__DOT__classification__DOT__high_index = 0;
    IData/*31:0*/ __Vdly__splitter__DOT__classification__DOT__low_index;
    __Vdly__splitter__DOT__classification__DOT__low_index = 0;
    IData/*31:0*/ __Vdly__splitter__DOT__classification__DOT__middle;
    __Vdly__splitter__DOT__classification__DOT__middle = 0;
    QData/*63:0*/ __Vdly__splitter__DOT__classification__DOT__base;
    __Vdly__splitter__DOT__classification__DOT__base = 0;
    IData/*31:0*/ __Vdly__splitter__DOT__classification__DOT__range_count;
    __Vdly__splitter__DOT__classification__DOT__range_count = 0;
    CData/*3:0*/ __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state;
    __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 0;
    VlWide<3>/*65:0*/ __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value;
    VL_ZERO_W(66, __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value);
    CData/*2:0*/ __Vdly__splitter__DOT__encoder__DOT__state;
    __Vdly__splitter__DOT__encoder__DOT__state = 0;
    CData/*2:0*/ __Vdly__splitter__DOT__encoder__DOT__remaining;
    __Vdly__splitter__DOT__encoder__DOT__remaining = 0;
    IData/*31:0*/ __Vdly__splitter__DOT__encoder__DOT__encoded;
    __Vdly__splitter__DOT__encoder__DOT__encoded = 0;
    CData/*0:0*/ __Vdly__splitter__DOT__encoder__DOT__final_scalar;
    __Vdly__splitter__DOT__encoder__DOT__final_scalar = 0;
    CData/*3:0*/ __Vdly__splitter__DOT__records__DOT__reader__DOT__state;
    __Vdly__splitter__DOT__records__DOT__reader__DOT__state = 0;
    VlWide<3>/*65:0*/ __Vdly__splitter__DOT__records__DOT__reader__DOT__offset_value;
    VL_ZERO_W(66, __Vdly__splitter__DOT__records__DOT__reader__DOT__offset_value);
    CData/*3:0*/ __Vdly__splitter__DOT__edges__DOT__reader__DOT__state;
    __Vdly__splitter__DOT__edges__DOT__reader__DOT__state = 0;
    VlWide<3>/*65:0*/ __Vdly__splitter__DOT__edges__DOT__reader__DOT__offset_value;
    VL_ZERO_W(66, __Vdly__splitter__DOT__edges__DOT__reader__DOT__offset_value);
    VlWide<3>/*95:0*/ __Vtemp_3;
    VlWide<3>/*95:0*/ __Vtemp_4;
    VlWide<3>/*95:0*/ __Vtemp_6;
    VlWide<3>/*95:0*/ __Vtemp_8;
    VlWide<3>/*95:0*/ __Vtemp_9;
    VlWide<3>/*95:0*/ __Vtemp_10;
    VlWide<3>/*95:0*/ __Vtemp_12;
    VlWide<3>/*95:0*/ __Vtemp_13;
    VlWide<3>/*95:0*/ __Vtemp_14;
    VlWide<3>/*95:0*/ __Vtemp_16;
    VlWide<3>/*95:0*/ __Vtemp_17;
    VlWide<3>/*95:0*/ __Vtemp_20;
    VlWide<3>/*95:0*/ __Vtemp_21;
    VlWide<3>/*95:0*/ __Vtemp_23;
    VlWide<3>/*95:0*/ __Vtemp_25;
    VlWide<3>/*95:0*/ __Vtemp_26;
    VlWide<3>/*95:0*/ __Vtemp_27;
    VlWide<3>/*95:0*/ __Vtemp_29;
    VlWide<3>/*95:0*/ __Vtemp_30;
    VlWide<3>/*95:0*/ __Vtemp_31;
    VlWide<3>/*95:0*/ __Vtemp_33;
    VlWide<3>/*95:0*/ __Vtemp_34;
    VlWide<3>/*95:0*/ __Vtemp_37;
    VlWide<3>/*95:0*/ __Vtemp_38;
    VlWide<3>/*95:0*/ __Vtemp_40;
    VlWide<3>/*95:0*/ __Vtemp_42;
    VlWide<3>/*95:0*/ __Vtemp_43;
    VlWide<3>/*95:0*/ __Vtemp_44;
    VlWide<3>/*95:0*/ __Vtemp_46;
    VlWide<3>/*95:0*/ __Vtemp_47;
    VlWide<3>/*95:0*/ __Vtemp_48;
    VlWide<3>/*95:0*/ __Vtemp_50;
    VlWide<3>/*95:0*/ __Vtemp_51;
    // Body
    __Vdly__splitter__DOT__encoder__DOT__final_scalar 
        = vlSelf->__PVT__splitter__DOT__encoder__DOT__final_scalar;
    __Vdly__splitter__DOT__encoder__DOT__encoded = vlSelf->__PVT__splitter__DOT__encoder__DOT__encoded;
    __Vdly__splitter__DOT__encoder__DOT__remaining 
        = vlSelf->__PVT__splitter__DOT__encoder__DOT__remaining;
    __Vdly__splitter__DOT__encoder__DOT__state = vlSelf->__PVT__splitter__DOT__encoder__DOT__state;
    __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[0U] 
        = vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[0U];
    __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[1U] 
        = vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[1U];
    __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[2U] 
        = vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[2U];
    __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state 
        = vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state;
    __Vdly__splitter__DOT__edges__DOT__reader__DOT__offset_value[0U] 
        = vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__offset_value[0U];
    __Vdly__splitter__DOT__edges__DOT__reader__DOT__offset_value[1U] 
        = vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__offset_value[1U];
    __Vdly__splitter__DOT__edges__DOT__reader__DOT__offset_value[2U] 
        = vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__offset_value[2U];
    __Vdly__splitter__DOT__edges__DOT__reader__DOT__state 
        = vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__state;
    __Vdly__splitter__DOT__classification__DOT__range_count 
        = vlSelf->__PVT__splitter__DOT__classification__DOT__range_count;
    __Vdly__splitter__DOT__classification__DOT__base 
        = vlSelf->__PVT__splitter__DOT__classification__DOT__base;
    __Vdly__splitter__DOT__classification__DOT__middle 
        = vlSelf->__PVT__splitter__DOT__classification__DOT__middle;
    __Vdly__splitter__DOT__classification__DOT__low_index 
        = vlSelf->__PVT__splitter__DOT__classification__DOT__low_index;
    __Vdly__splitter__DOT__classification__DOT__high_index 
        = vlSelf->__PVT__splitter__DOT__classification__DOT__high_index;
    __Vdly__splitter__DOT__classification__DOT__state 
        = vlSelf->__PVT__splitter__DOT__classification__DOT__state;
    __Vdly__splitter__DOT__encoded_remaining = vlSelf->__PVT__splitter__DOT__encoded_remaining;
    __Vdly__splitter__DOT__edge_cursor = vlSelf->__PVT__splitter__DOT__edge_cursor;
    __Vdly__splitter__DOT__output_index = vlSelf->__PVT__splitter__DOT__output_index;
    __Vdly__splitter__DOT__plan_count = vlSelf->__PVT__splitter__DOT__plan_count;
    __Vdly__splitter__DOT__byte_count = vlSelf->__PVT__splitter__DOT__byte_count;
    __Vdly__splitter__DOT__output_last = vlSelf->__PVT__splitter__DOT__output_last;
    __Vdlyvset__splitter__DOT__scalar_starts__v0 = 0U;
    __Vdly__splitter__DOT__edge_first = vlSelf->__PVT__splitter__DOT__edge_first;
    __Vdly__splitter__DOT__scalar_index = vlSelf->__PVT__splitter__DOT__scalar_index;
    __Vdlyvset__splitter__DOT__plan_value__v0 = 0U;
    __Vdlyvset__splitter__DOT__plan_value__v1 = 0U;
    __Vdlyvset__splitter__DOT__scalars__v0 = 0U;
    __Vdlyvset__splitter__DOT__plan_special__v0 = 0U;
    __Vdlyvset__splitter__DOT__plan_special__v1 = 0U;
    __Vdly__splitter__DOT__scan_index = vlSelf->__PVT__splitter__DOT__scan_index;
    __Vdly__splitter__DOT__scalar_count = vlSelf->__PVT__splitter__DOT__scalar_count;
    __Vdlyvset__splitter__DOT__properties__v0 = 0U;
    __Vdlyvset__splitter__DOT__bytes_memory__v0 = 0U;
    __Vdly__splitter__DOT__cursor = vlSelf->__PVT__splitter__DOT__cursor;
    __Vdly__splitter__DOT__state = vlSelf->__PVT__splitter__DOT__state;
    __Vdly__splitter__DOT__records__DOT__reader__DOT__offset_value[0U] 
        = vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__offset_value[0U];
    __Vdly__splitter__DOT__records__DOT__reader__DOT__offset_value[1U] 
        = vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__offset_value[1U];
    __Vdly__splitter__DOT__records__DOT__reader__DOT__offset_value[2U] 
        = vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__offset_value[2U];
    __Vdly__splitter__DOT__records__DOT__reader__DOT__state 
        = vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__state;
    if (vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) {
        if ((8U & (IData)(vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__state))) {
            if ((4U & (IData)(vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__state))) {
                vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__failed = 1U;
                vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__code = 0x11U;
                __Vdly__splitter__DOT__records__DOT__reader__DOT__state = 0xaU;
            } else if ((2U & (IData)(vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__state))) {
                    vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__failed = 1U;
                    vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__code = 0x11U;
                    __Vdly__splitter__DOT__records__DOT__reader__DOT__state = 0xaU;
                } else if (((IData)(vlSelf->__PVT__splitter__DOT__record_valid) 
                            & ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                               & ((9U == (IData)(vlSelf->__PVT__splitter__DOT__state)) 
                                  | (0xcU == (IData)(vlSelf->__PVT__splitter__DOT__state)))))) {
                    __Vdly__splitter__DOT__records__DOT__reader__DOT__state = 0U;
                }
            } else if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__state))) {
                VL_ASSIGNSEL_WI(128,32,(0x7fU & VL_SHIFTL_III(7,32,32, (IData)(vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__word_index), 5U)), vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__result_data, vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__read_data);
                if ((3U == (IData)(vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__word_index))) {
                    __Vdly__splitter__DOT__records__DOT__reader__DOT__state = 0xaU;
                } else {
                    vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__word_index 
                        = (3U & ((IData)(1U) + (IData)(vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__word_index)));
                    __Vtemp_3[0U] = 4U;
                    __Vtemp_3[1U] = 0U;
                    __Vtemp_3[2U] = 0U;
                    VL_ADD_W(3, __Vtemp_4, __Vtemp_3, vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__offset_value);
                    __Vdly__splitter__DOT__records__DOT__reader__DOT__offset_value[0U] 
                        = __Vtemp_4[0U];
                    __Vdly__splitter__DOT__records__DOT__reader__DOT__offset_value[1U] 
                        = __Vtemp_4[1U];
                    __Vdly__splitter__DOT__records__DOT__reader__DOT__offset_value[2U] 
                        = (3U & __Vtemp_4[2U]);
                    __Vdly__splitter__DOT__records__DOT__reader__DOT__state = 5U;
                }
            } else if ((((IData)(vlSelf->__VdfgTmp_hed1c005a__0) 
                         & (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalized_specials__tbl_rsp_valid)) 
                        & (IData)(vlSelf->__PVT__splitter__DOT__record_rsp_ready))) {
                if (vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer_rsp_error) {
                    vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__failed = 1U;
                    vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__code = 4U;
                    __Vdly__splitter__DOT__records__DOT__reader__DOT__state = 0xaU;
                } else {
                    vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__read_data 
                        = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer_rsp_data;
                    __Vdly__splitter__DOT__records__DOT__reader__DOT__state = 9U;
                }
            }
        } else if ((4U & (IData)(vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__state))) {
            if ((2U & (IData)(vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__state))) {
                    if (((IData)(vlSelf->__PVT__splitter__DOT__record_req) 
                         & ((IData)(vlSelf->__VdfgTmp_hed1c005a__0) 
                            & (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalized_specials__tbl_req_ready)))) {
                        __Vdly__splitter__DOT__records__DOT__reader__DOT__state = 8U;
                    }
                } else if ((IData)(((0U != vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__request_address[2U]) 
                                    | VL_GTE_W(3, vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__request_address, vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__table_end)))) {
                    vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__failed = 1U;
                    vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__code = 0x11U;
                    __Vdly__splitter__DOT__records__DOT__reader__DOT__state = 0xaU;
                } else {
                    __Vdly__splitter__DOT__records__DOT__reader__DOT__state = 7U;
                }
            } else if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__state))) {
                VL_ADD_W(3, __Vtemp_6, vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__data_start, vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__offset_value);
                vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__request_address[0U] 
                    = __Vtemp_6[0U];
                vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__request_address[1U] 
                    = __Vtemp_6[1U];
                vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__request_address[2U] 
                    = (3U & __Vtemp_6[2U]);
                __Vdly__splitter__DOT__records__DOT__reader__DOT__state = 6U;
            } else if ((IData)(((((0ULL != (3ULL & vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__base)) 
                                  | (0U != vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__data_start[2U])) 
                                 | (0U != vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__table_end[2U])) 
                                | ((0U == vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__count) 
                                   | (vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__index 
                                      >= vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__count))))) {
                vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__failed = 1U;
                vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__code = 0x11U;
                __Vdly__splitter__DOT__records__DOT__reader__DOT__state = 0xaU;
            } else {
                __Vdly__splitter__DOT__records__DOT__reader__DOT__state = 5U;
            }
        } else if ((2U & (IData)(vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__state))) {
            if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__state))) {
                __Vtemp_8[0U] = vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__count;
                __Vtemp_8[1U] = 0U;
                __Vtemp_8[2U] = 0U;
                VL_SHIFTL_WWI(66,66,32, __Vtemp_9, __Vtemp_8, 4U);
                VL_ADD_W(3, __Vtemp_10, vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__data_start, __Vtemp_9);
                vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__table_end[0U] 
                    = __Vtemp_10[0U];
                vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__table_end[1U] 
                    = __Vtemp_10[1U];
                vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__table_end[2U] 
                    = (3U & __Vtemp_10[2U]);
                __Vdly__splitter__DOT__records__DOT__reader__DOT__state = 4U;
            } else {
                __Vtemp_12[0U] = 0x20U;
                __Vtemp_12[1U] = 0U;
                __Vtemp_12[2U] = 0U;
                __Vtemp_13[0U] = (IData)(vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__base);
                __Vtemp_13[1U] = (IData)((vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__base 
                                          >> 0x20U));
                __Vtemp_13[2U] = 0U;
                VL_ADD_W(3, __Vtemp_14, __Vtemp_12, __Vtemp_13);
                vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__data_start[0U] 
                    = __Vtemp_14[0U];
                vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__data_start[1U] 
                    = __Vtemp_14[1U];
                vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__data_start[2U] 
                    = (3U & __Vtemp_14[2U]);
                __Vdly__splitter__DOT__records__DOT__reader__DOT__state = 3U;
            }
        } else if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__state))) {
            __Vtemp_16[0U] = vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__index;
            __Vtemp_16[1U] = 0U;
            __Vtemp_16[2U] = 0U;
            VL_SHIFTL_WWI(66,66,32, __Vtemp_17, __Vtemp_16, 4U);
            __Vdly__splitter__DOT__records__DOT__reader__DOT__offset_value[0U] 
                = __Vtemp_17[0U];
            __Vdly__splitter__DOT__records__DOT__reader__DOT__offset_value[1U] 
                = __Vtemp_17[1U];
            __Vdly__splitter__DOT__records__DOT__reader__DOT__offset_value[2U] 
                = (3U & __Vtemp_17[2U]);
            __Vdly__splitter__DOT__records__DOT__reader__DOT__state = 2U;
        } else if ((((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                     & ((8U == (IData)(vlSelf->__PVT__splitter__DOT__state)) 
                        | (0xbU == (IData)(vlSelf->__PVT__splitter__DOT__state)))) 
                    & (IData)(vlSelf->__PVT__splitter__DOT__record_ready))) {
            vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__word_index = 0U;
            if (vlSelf->__PVT__splitter__DOT__special_selected) {
                vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__base 
                    = (((QData)((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__table_bases[0x15U])) 
                        << 0x20U) | (QData)((IData)(
                                                    vlSymsp->TOP.bench__DOT__dut__DOT__table_bases[0x14U])));
                vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__count 
                    = vlSymsp->TOP.bench__DOT__dut__DOT__committed_counts[0xaU];
                vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__index 
                    = vlSelf->__PVT__splitter__DOT__terminal_index;
            } else {
                vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__base 
                    = (((QData)((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__table_bases[0xbU])) 
                        << 0x20U) | (QData)((IData)(
                                                    vlSymsp->TOP.bench__DOT__dut__DOT__table_bases[0xaU])));
                vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__count 
                    = vlSymsp->TOP.bench__DOT__dut__DOT__committed_counts[5U];
                vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__index 
                    = vlSelf->__PVT__splitter__DOT__node_index;
            }
            vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__result_data[0U] = 0U;
            vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__result_data[1U] = 0U;
            vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__result_data[2U] = 0U;
            vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__result_data[3U] = 0U;
            vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__failed = 0U;
            vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__code = 0U;
            __Vdly__splitter__DOT__records__DOT__reader__DOT__state = 1U;
        }
        if (((IData)(vlSelf->__PVT__busy) & ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                                             & (4U 
                                                == (IData)(vlSelf->__PVT__splitter__DOT__encoder__DOT__state))))) {
            vlSelf->__PVT__splitter__DOT__code = ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n)
                                                   ? (IData)(vlSelf->__PVT__splitter__DOT__encoder__DOT__code)
                                                   : 0U);
            __Vdly__splitter__DOT__state = 0x19U;
        } else if ((0x20U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
            vlSelf->__PVT__splitter__DOT__code = 0x12U;
            __Vdly__splitter__DOT__state = 0x19U;
        } else if ((0x10U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
            if ((8U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                if ((4U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                    vlSelf->__PVT__splitter__DOT__code = 0x12U;
                    __Vdly__splitter__DOT__state = 0x19U;
                } else if ((2U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                    if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                        vlSelf->__PVT__splitter__DOT__code = 0x12U;
                        __Vdly__splitter__DOT__state = 0x19U;
                    } else {
                        vlSelf->__PVT__splitter__DOT__output_value 
                            = vlSelf->__PVT__splitter__DOT__plan_value
                            [(0xfU & vlSelf->__PVT__splitter__DOT__output_index)];
                        vlSelf->__PVT__splitter__DOT__output_special 
                            = vlSelf->__PVT__splitter__DOT__plan_special
                            [(0xfU & vlSelf->__PVT__splitter__DOT__output_index)];
                        __Vdly__splitter__DOT__output_last 
                            = (((IData)(1U) + vlSelf->__PVT__splitter__DOT__output_index) 
                               == vlSelf->__PVT__splitter__DOT__plan_count);
                        vlSelf->__PVT__splitter__DOT__output_boundary 
                            = ((~ vlSelf->__PVT__splitter__DOT__plan_special
                                [(0xfU & vlSelf->__PVT__splitter__DOT__output_index)]) 
                               & ((((IData)(1U) + vlSelf->__PVT__splitter__DOT__output_index) 
                                   == vlSelf->__PVT__splitter__DOT__plan_count) 
                                  | vlSelf->__PVT__splitter__DOT__plan_special
                                  [(0xfU & ((IData)(1U) 
                                            + vlSelf->__PVT__splitter__DOT__output_index))]));
                        __Vdly__splitter__DOT__state = 0x17U;
                    }
                } else if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                    __Vdly__splitter__DOT__state = 0x19U;
                } else if (vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__start) {
                    if ((1U & (((~ (IData)(vlSymsp->TOP.bench__DOT__boot_done)) 
                                | (2U < vlSymsp->TOP.bench__DOT__dut__DOT__committed_metadata[4U])) 
                               | (vlSymsp->TOP.bench__DOT__dut__DOT__committed_metadata[0xdU] 
                                  >= vlSymsp->TOP.bench__DOT__dut__DOT__committed_counts[5U])))) {
                        vlSelf->__PVT__splitter__DOT__code = 6U;
                        __Vdly__splitter__DOT__state = 0x19U;
                    } else {
                        __Vdly__splitter__DOT__scalar_count = 0U;
                        __Vdly__splitter__DOT__scalar_index = 0U;
                        __Vdly__splitter__DOT__byte_count = 0U;
                        __Vdly__splitter__DOT__scan_index = 0U;
                        __Vdly__splitter__DOT__plan_count = 0U;
                        __Vdly__splitter__DOT__output_index = 0U;
                        vlSelf->__PVT__splitter__DOT__phase = 1U;
                        vlSelf->__PVT__splitter__DOT__code = 0U;
                        __Vdly__splitter__DOT__state = 1U;
                    }
                }
            } else if ((4U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                if ((2U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                    if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                        if (((IData)(vlSelf->out_valid) 
                             & ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                                & (((9U == (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__state)) 
                                    & (IData)(vlSelf->out_special)) 
                                   | ((0xbU == (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__state)) 
                                      & (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__span_ready)))))) {
                            if (vlSelf->__PVT__splitter__DOT__output_last) {
                                __Vdly__splitter__DOT__state = 0x18U;
                            } else {
                                __Vdly__splitter__DOT__output_index 
                                    = ((IData)(1U) 
                                       + vlSelf->__PVT__splitter__DOT__output_index);
                                __Vdly__splitter__DOT__state = 0x1aU;
                            }
                        }
                    } else if ((0x10U <= vlSelf->__PVT__splitter__DOT__plan_count)) {
                        vlSelf->__PVT__splitter__DOT__code = 0x30U;
                        __Vdly__splitter__DOT__state = 0x19U;
                    } else {
                        __Vdlyvval__splitter__DOT__plan_value__v0 
                            = vlSelf->__PVT__splitter__DOT__scalars
                            [(0xfU & vlSelf->__PVT__splitter__DOT__scan_index)];
                        __Vdlyvset__splitter__DOT__plan_value__v0 = 1U;
                        __Vdlyvdim0__splitter__DOT__plan_value__v0 
                            = (0xfU & vlSelf->__PVT__splitter__DOT__plan_count);
                        __Vdly__splitter__DOT__state = 7U;
                        __Vdlyvset__splitter__DOT__plan_special__v0 = 1U;
                        __Vdlyvdim0__splitter__DOT__plan_special__v0 
                            = (0xfU & vlSelf->__PVT__splitter__DOT__plan_count);
                        __Vdlyvval__splitter__DOT__plan_space__v0 
                            = (1U & (vlSelf->__PVT__splitter__DOT__properties
                                     [(0xfU & vlSelf->__PVT__splitter__DOT__scan_index)] 
                                     >> 8U));
                        __Vdlyvdim0__splitter__DOT__plan_space__v0 
                            = (0xfU & vlSelf->__PVT__splitter__DOT__plan_count);
                        __Vdly__splitter__DOT__plan_count 
                            = ((IData)(1U) + vlSelf->__PVT__splitter__DOT__plan_count);
                        __Vdly__splitter__DOT__scan_index 
                            = ((IData)(1U) + vlSelf->__PVT__splitter__DOT__scan_index);
                    }
                } else if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                    if ((((vlSelf->__PVT__splitter__DOT__best_flags 
                           >> 2U) & (vlSelf->__PVT__splitter__DOT__scan_index 
                                     < vlSelf->__PVT__splitter__DOT__scalar_count)) 
                         & (vlSelf->__PVT__splitter__DOT__properties
                            [(0xfU & vlSelf->__PVT__splitter__DOT__scan_index)] 
                            >> 8U))) {
                        __Vdly__splitter__DOT__scan_index 
                            = ((IData)(1U) + vlSelf->__PVT__splitter__DOT__scan_index);
                    } else {
                        __Vdly__splitter__DOT__state = 7U;
                    }
                } else if ((0x10U <= vlSelf->__PVT__splitter__DOT__plan_count)) {
                    vlSelf->__PVT__splitter__DOT__code = 0x30U;
                    __Vdly__splitter__DOT__state = 0x19U;
                } else {
                    __Vdlyvval__splitter__DOT__plan_value__v1 
                        = vlSelf->__PVT__splitter__DOT__best_token;
                    __Vdlyvset__splitter__DOT__plan_value__v1 = 1U;
                    __Vdlyvdim0__splitter__DOT__plan_value__v1 
                        = (0xfU & vlSelf->__PVT__splitter__DOT__plan_count);
                    __Vdly__splitter__DOT__scan_index 
                        = vlSelf->__PVT__splitter__DOT__best_end;
                    __Vdly__splitter__DOT__state = 0x15U;
                    __Vdlyvset__splitter__DOT__plan_special__v1 = 1U;
                    __Vdlyvdim0__splitter__DOT__plan_special__v1 
                        = (0xfU & vlSelf->__PVT__splitter__DOT__plan_count);
                    __Vdlyvdim0__splitter__DOT__plan_space__v1 
                        = (0xfU & vlSelf->__PVT__splitter__DOT__plan_count);
                    __Vdly__splitter__DOT__plan_count 
                        = ((IData)(1U) + vlSelf->__PVT__splitter__DOT__plan_count);
                }
            } else if ((2U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                    if (((((vlSelf->__PVT__splitter__DOT__best_flags 
                            >> 1U) & (0U != vlSelf->__PVT__splitter__DOT__plan_count)) 
                          & (~ vlSelf->__PVT__splitter__DOT__plan_special
                             [(0xfU & (vlSelf->__PVT__splitter__DOT__plan_count 
                                       - (IData)(1U)))])) 
                         & vlSelf->__PVT__splitter__DOT__plan_space
                         [(0xfU & (vlSelf->__PVT__splitter__DOT__plan_count 
                                   - (IData)(1U)))])) {
                        __Vdly__splitter__DOT__plan_count 
                            = (vlSelf->__PVT__splitter__DOT__plan_count 
                               - (IData)(1U));
                    } else {
                        __Vdly__splitter__DOT__state = 0x14U;
                    }
                } else if (vlSelf->__PVT__splitter__DOT__best_valid) {
                    if ((2U == vlSymsp->TOP.bench__DOT__dut__DOT__committed_metadata[4U])) {
                        vlSelf->__PVT__splitter__DOT__code = 0x13U;
                        __Vdly__splitter__DOT__state = 0x19U;
                    } else {
                        __Vdly__splitter__DOT__state = 0x13U;
                    }
                } else {
                    __Vdly__splitter__DOT__state = 0x16U;
                }
            } else if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                if (((0xffU < (IData)(vlSelf->__PVT__splitter__DOT__edge_record)) 
                     | ((IData)((vlSelf->__PVT__splitter__DOT__edge_record 
                                 >> 0x20U)) >= vlSymsp->TOP.bench__DOT__dut__DOT__committed_counts[5U]))) {
                    vlSelf->__PVT__splitter__DOT__code = 0x12U;
                    __Vdly__splitter__DOT__state = 0x19U;
                } else if (((0xffU & (IData)(vlSelf->__PVT__splitter__DOT__edge_record)) 
                            == vlSelf->__PVT__splitter__DOT__bytes_memory
                            [(0xfU & vlSelf->__PVT__splitter__DOT__cursor)])) {
                    __Vdly__splitter__DOT__cursor = 
                        ((IData)(1U) + vlSelf->__PVT__splitter__DOT__cursor);
                    vlSelf->__PVT__splitter__DOT__node_index 
                        = (IData)((vlSelf->__PVT__splitter__DOT__edge_record 
                                   >> 0x20U));
                    __Vdly__splitter__DOT__state = 8U;
                } else if (((0xffU & (IData)(vlSelf->__PVT__splitter__DOT__edge_record)) 
                            > vlSelf->__PVT__splitter__DOT__bytes_memory
                            [(0xfU & vlSelf->__PVT__splitter__DOT__cursor)])) {
                    __Vdly__splitter__DOT__state = 0x12U;
                } else {
                    __Vdly__splitter__DOT__edge_cursor 
                        = ((IData)(1U) + vlSelf->__PVT__splitter__DOT__edge_cursor);
                    __Vdly__splitter__DOT__state = 0xeU;
                }
            } else if (vlSelf->__PVT__splitter__DOT__edge_valid) {
                if (((IData)(vlSelf->__PVT__splitter__DOT__edge_valid) 
                     & (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__failed))) {
                    vlSelf->__PVT__splitter__DOT__code 
                        = ((IData)(vlSelf->__PVT__splitter__DOT__edge_valid)
                            ? (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__code)
                            : 0U);
                    __Vdly__splitter__DOT__state = 0x19U;
                } else {
                    vlSelf->__PVT__splitter__DOT__edge_record 
                        = (((~ (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__failed)) 
                            & (IData)(vlSelf->__PVT__splitter__DOT__edge_valid))
                            ? vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__result_data
                            : 0ULL);
                    __Vdly__splitter__DOT__state = 0x11U;
                }
            }
        } else if ((8U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
            if ((4U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                if ((2U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                    if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                        if (vlSelf->__PVT__splitter__DOT__edge_ready) {
                            __Vdly__splitter__DOT__state = 0x10U;
                        }
                    } else if ((vlSelf->__PVT__splitter__DOT__edge_end 
                                > (QData)((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__committed_counts[6U])))) {
                        vlSelf->__PVT__splitter__DOT__code = 0x12U;
                        __Vdly__splitter__DOT__state = 0x19U;
                    } else {
                        __Vdly__splitter__DOT__state 
                            = (((vlSelf->__PVT__splitter__DOT__cursor 
                                 == vlSelf->__PVT__splitter__DOT__byte_count) 
                                | (vlSelf->__PVT__splitter__DOT__edge_cursor 
                                   == vlSelf->__PVT__splitter__DOT__edge_count))
                                ? 0x12U : 0xfU);
                    }
                } else if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                    if ((((0ULL != (((QData)((IData)(
                                                     vlSelf->__PVT__splitter__DOT__special_record[3U])) 
                                     << 0x20U) | (QData)((IData)(
                                                                 vlSelf->__PVT__splitter__DOT__special_record[2U])))) 
                          | (0U != (vlSelf->__PVT__splitter__DOT__special_flags 
                                    >> 5U))) | (vlSelf->__PVT__splitter__DOT__special_record[0U] 
                                                >= 
                                                vlSymsp->TOP.bench__DOT__dut__DOT__committed_metadata[2U]))) {
                        vlSelf->__PVT__splitter__DOT__code = 0x12U;
                        __Vdly__splitter__DOT__state = 0x19U;
                    } else {
                        if (((IData)(vlSelf->__PVT__splitter__DOT__eligible) 
                             & (((~ (IData)(vlSelf->__PVT__splitter__DOT__best_valid)) 
                                 | (vlSelf->__PVT__splitter__DOT__terminal_end 
                                    > vlSelf->__PVT__splitter__DOT__best_end)) 
                                | ((vlSelf->__PVT__splitter__DOT__terminal_end 
                                    == vlSelf->__PVT__splitter__DOT__best_end) 
                                   & (vlSelf->__PVT__splitter__DOT__terminal_index 
                                      < vlSelf->__PVT__splitter__DOT__best_record))))) {
                            vlSelf->__PVT__splitter__DOT__best_valid = 1U;
                            vlSelf->__PVT__splitter__DOT__best_end 
                                = vlSelf->__PVT__splitter__DOT__terminal_end;
                            vlSelf->__PVT__splitter__DOT__best_token 
                                = vlSelf->__PVT__splitter__DOT__special_record[0U];
                            vlSelf->__PVT__splitter__DOT__best_flags 
                                = vlSelf->__PVT__splitter__DOT__special_flags;
                            vlSelf->__PVT__splitter__DOT__best_record 
                                = vlSelf->__PVT__splitter__DOT__terminal_index;
                        }
                        __Vdly__splitter__DOT__state = 0xeU;
                    }
                } else if (vlSelf->__PVT__splitter__DOT__record_valid) {
                    if (vlSelf->__PVT__splitter__DOT__record_error) {
                        vlSelf->__PVT__splitter__DOT__code 
                            = vlSelf->__PVT__splitter__DOT__record_code;
                        __Vdly__splitter__DOT__state = 0x19U;
                    } else {
                        vlSelf->__PVT__splitter__DOT__special_record[0U] 
                            = vlSelf->__PVT__splitter__DOT__record_data[0U];
                        vlSelf->__PVT__splitter__DOT__special_record[1U] 
                            = vlSelf->__PVT__splitter__DOT__record_data[1U];
                        vlSelf->__PVT__splitter__DOT__special_record[2U] 
                            = vlSelf->__PVT__splitter__DOT__record_data[2U];
                        vlSelf->__PVT__splitter__DOT__special_record[3U] 
                            = vlSelf->__PVT__splitter__DOT__record_data[3U];
                        __Vdly__splitter__DOT__state = 0xdU;
                    }
                }
            } else if ((2U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                    if (vlSelf->__PVT__splitter__DOT__record_ready) {
                        __Vdly__splitter__DOT__state = 0xcU;
                    }
                } else {
                    __Vdly__splitter__DOT__edge_cursor = 0U;
                    __Vdly__splitter__DOT__edge_first 
                        = vlSelf->__PVT__splitter__DOT__node_record[0U];
                    vlSelf->__PVT__splitter__DOT__edge_count 
                        = vlSelf->__PVT__splitter__DOT__node_record[1U];
                    vlSelf->__PVT__splitter__DOT__terminal_index 
                        = vlSelf->__PVT__splitter__DOT__node_record[2U];
                    if ((0U != vlSelf->__PVT__splitter__DOT__node_record[3U])) {
                        vlSelf->__PVT__splitter__DOT__code = 0x12U;
                        __Vdly__splitter__DOT__state = 0x19U;
                    } else {
                        __Vdly__splitter__DOT__state 
                            = ((((vlSelf->__PVT__splitter__DOT__cursor 
                                  > vlSelf->__PVT__splitter__DOT__scalar_starts
                                  [(0xfU & vlSelf->__PVT__splitter__DOT__scan_index)]) 
                                 & (0U != vlSelf->__PVT__splitter__DOT__terminal_end)) 
                                & (0xffffffffU != vlSelf->__PVT__splitter__DOT__node_record[2U]))
                                ? 0xbU : 0xeU);
                    }
                }
            } else if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                if (vlSelf->__PVT__splitter__DOT__record_valid) {
                    if (vlSelf->__PVT__splitter__DOT__record_error) {
                        vlSelf->__PVT__splitter__DOT__code 
                            = vlSelf->__PVT__splitter__DOT__record_code;
                        __Vdly__splitter__DOT__state = 0x19U;
                    } else {
                        vlSelf->__PVT__splitter__DOT__node_record[0U] 
                            = vlSelf->__PVT__splitter__DOT__record_data[0U];
                        vlSelf->__PVT__splitter__DOT__node_record[1U] 
                            = vlSelf->__PVT__splitter__DOT__record_data[1U];
                        vlSelf->__PVT__splitter__DOT__node_record[2U] 
                            = vlSelf->__PVT__splitter__DOT__record_data[2U];
                        vlSelf->__PVT__splitter__DOT__node_record[3U] 
                            = vlSelf->__PVT__splitter__DOT__record_data[3U];
                        __Vdly__splitter__DOT__state = 0xaU;
                    }
                }
            } else if (vlSelf->__PVT__splitter__DOT__record_ready) {
                __Vdly__splitter__DOT__state = 9U;
            }
        } else if ((4U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
            if ((2U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                    if ((vlSelf->__PVT__splitter__DOT__scan_index 
                         == vlSelf->__PVT__splitter__DOT__scalar_count)) {
                        __Vdly__splitter__DOT__output_index = 0U;
                        __Vdly__splitter__DOT__state = 0x1aU;
                    } else if ((0U == vlSymsp->TOP.bench__DOT__dut__DOT__committed_metadata[4U])) {
                        __Vdly__splitter__DOT__state = 0x16U;
                    } else {
                        __Vdly__splitter__DOT__cursor 
                            = vlSelf->__PVT__splitter__DOT__scalar_starts
                            [(0xfU & vlSelf->__PVT__splitter__DOT__scan_index)];
                        vlSelf->__PVT__splitter__DOT__node_index 
                            = vlSymsp->TOP.bench__DOT__dut__DOT__committed_metadata[0xdU];
                        vlSelf->__PVT__splitter__DOT__best_valid = 0U;
                        __Vdly__splitter__DOT__state = 8U;
                    }
                } else if (vlSelf->__PVT__splitter__DOT__encoder_valid) {
                    if ((0x10U <= vlSelf->__PVT__splitter__DOT__byte_count)) {
                        vlSelf->__PVT__splitter__DOT__code = 0x30U;
                        __Vdly__splitter__DOT__state = 0x19U;
                    } else {
                        __Vdlyvval__splitter__DOT__bytes_memory__v0 
                            = ((IData)(vlSelf->__PVT__splitter__DOT__encoder_valid)
                                ? (0xffU & vlSelf->__PVT__splitter__DOT__encoder__DOT__encoded)
                                : 0U);
                        __Vdlyvset__splitter__DOT__bytes_memory__v0 = 1U;
                        __Vdlyvdim0__splitter__DOT__bytes_memory__v0 
                            = (0xfU & vlSelf->__PVT__splitter__DOT__byte_count);
                        if ((1U == (IData)(vlSelf->__PVT__splitter__DOT__encoded_remaining))) {
                            __Vdlyvval__splitter__DOT__byte_ends__v0 
                                = ((IData)(1U) + vlSelf->__PVT__splitter__DOT__scalar_index);
                            if ((((IData)(1U) + vlSelf->__PVT__splitter__DOT__scalar_index) 
                                 == vlSelf->__PVT__splitter__DOT__scalar_count)) {
                                __Vdly__splitter__DOT__state = 7U;
                            } else {
                                __Vdly__splitter__DOT__scalar_index 
                                    = ((IData)(1U) 
                                       + vlSelf->__PVT__splitter__DOT__scalar_index);
                                __Vdly__splitter__DOT__state = 5U;
                            }
                        } else {
                            __Vdlyvval__splitter__DOT__byte_ends__v0 = 0U;
                        }
                        __Vdlyvdim0__splitter__DOT__byte_ends__v0 
                            = (0xfU & vlSelf->__PVT__splitter__DOT__byte_count);
                        __Vdly__splitter__DOT__byte_count 
                            = ((IData)(1U) + vlSelf->__PVT__splitter__DOT__byte_count);
                        __Vdly__splitter__DOT__encoded_remaining 
                            = (7U & ((IData)(vlSelf->__PVT__splitter__DOT__encoded_remaining) 
                                     - (IData)(1U)));
                    }
                }
            } else if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                if (vlSelf->__PVT__splitter__DOT__encoder_ready) {
                    __Vdlyvval__splitter__DOT__scalar_starts__v0 
                        = vlSelf->__PVT__splitter__DOT__byte_count;
                    __Vdlyvset__splitter__DOT__scalar_starts__v0 = 1U;
                    __Vdlyvdim0__splitter__DOT__scalar_starts__v0 
                        = (0xfU & vlSelf->__PVT__splitter__DOT__scalar_index);
                    __Vdly__splitter__DOT__state = 6U;
                    __Vdly__splitter__DOT__encoded_remaining 
                        = ((0x80U > vlSelf->__PVT__splitter__DOT__scalars
                            [(0xfU & vlSelf->__PVT__splitter__DOT__scalar_index)])
                            ? 1U : ((0x800U > vlSelf->__PVT__splitter__DOT__scalars
                                     [(0xfU & vlSelf->__PVT__splitter__DOT__scalar_index)])
                                     ? 2U : ((0x10000U 
                                              > vlSelf->__PVT__splitter__DOT__scalars
                                              [(0xfU 
                                                & vlSelf->__PVT__splitter__DOT__scalar_index)])
                                              ? 3U : 4U)));
                }
            } else {
                __Vdly__splitter__DOT__state = 5U;
            }
        } else if ((2U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
            if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
                if (vlSelf->__PVT__splitter__DOT__class_valid) {
                    if (((IData)(vlSelf->__PVT__splitter__DOT__class_valid) 
                         & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__failed))) {
                        vlSelf->__PVT__splitter__DOT__code 
                            = ((IData)(vlSelf->__PVT__splitter__DOT__class_valid)
                                ? (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__code)
                                : 0U);
                        __Vdly__splitter__DOT__state = 0x19U;
                    } else {
                        __Vdlyvval__splitter__DOT__properties__v0 
                            = (((~ (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__failed)) 
                                & (IData)(vlSelf->__PVT__splitter__DOT__class_valid))
                                ? (0x3ffU & vlSelf->__PVT__splitter__DOT__classification__DOT__property_value)
                                : 0U);
                        __Vdlyvset__splitter__DOT__properties__v0 = 1U;
                        __Vdlyvdim0__splitter__DOT__properties__v0 
                            = (0xfU & vlSelf->__PVT__splitter__DOT__scalar_index);
                        if ((((IData)(1U) + vlSelf->__PVT__splitter__DOT__scalar_index) 
                             == vlSelf->__PVT__splitter__DOT__scalar_count)) {
                            __Vdly__splitter__DOT__scalar_index = 0U;
                            __Vdly__splitter__DOT__state = 4U;
                        } else {
                            __Vdly__splitter__DOT__scalar_index 
                                = ((IData)(1U) + vlSelf->__PVT__splitter__DOT__scalar_index);
                            __Vdly__splitter__DOT__state = 2U;
                        }
                    }
                }
            } else if (vlSelf->__PVT__splitter__DOT__class_ready) {
                __Vdly__splitter__DOT__state = 3U;
            }
        } else if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__state))) {
            if ((((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____VdfgTmp_h67e2c008__0) 
                  & (IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalization.out_valid)) 
                 & (IData)(vlSelf->in_ready))) {
                if ((0x10U <= vlSelf->__PVT__splitter__DOT__scalar_count)) {
                    vlSelf->__PVT__splitter__DOT__code = 0x30U;
                    __Vdly__splitter__DOT__state = 0x19U;
                } else {
                    __Vdlyvval__splitter__DOT__scalars__v0 
                        = ((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalization.out_valid)
                            ? vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalization.__PVT__normalizer__DOT__scalars
                           [(0xfU & vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalization.__PVT__normalizer__DOT__output_index)]
                            : 0U);
                    __Vdlyvset__splitter__DOT__scalars__v0 = 1U;
                    __Vdlyvdim0__splitter__DOT__scalars__v0 
                        = (0xfU & vlSelf->__PVT__splitter__DOT__scalar_count);
                    __Vdly__splitter__DOT__scalar_count 
                        = ((IData)(1U) + vlSelf->__PVT__splitter__DOT__scalar_count);
                    if (vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalization.out_last) {
                        __Vdly__splitter__DOT__scalar_index = 0U;
                        __Vdly__splitter__DOT__state = 2U;
                    } else if ((0x10U == ((IData)(1U) 
                                          + vlSelf->__PVT__splitter__DOT__scalar_count))) {
                        vlSelf->__PVT__splitter__DOT__code = 0x30U;
                        __Vdly__splitter__DOT__state = 0x19U;
                    }
                }
            }
        } else if (vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__start) {
            if ((1U & (((~ (IData)(vlSymsp->TOP.bench__DOT__boot_done)) 
                        | (2U < vlSymsp->TOP.bench__DOT__dut__DOT__committed_metadata[4U])) 
                       | (vlSymsp->TOP.bench__DOT__dut__DOT__committed_metadata[0xdU] 
                          >= vlSymsp->TOP.bench__DOT__dut__DOT__committed_counts[5U])))) {
                vlSelf->__PVT__splitter__DOT__code = 6U;
                __Vdly__splitter__DOT__state = 0x19U;
            } else {
                __Vdly__splitter__DOT__scalar_count = 0U;
                __Vdly__splitter__DOT__scalar_index = 0U;
                __Vdly__splitter__DOT__byte_count = 0U;
                __Vdly__splitter__DOT__scan_index = 0U;
                __Vdly__splitter__DOT__plan_count = 0U;
                __Vdly__splitter__DOT__output_index = 0U;
                vlSelf->__PVT__splitter__DOT__phase = 1U;
                vlSelf->__PVT__splitter__DOT__code = 0U;
                __Vdly__splitter__DOT__state = 1U;
            }
        }
        if ((4U & (IData)(vlSelf->__PVT__splitter__DOT__encoder__DOT__state))) {
            if ((2U & (IData)(vlSelf->__PVT__splitter__DOT__encoder__DOT__state))) {
                vlSelf->__PVT__splitter__DOT__encoder__DOT__code = 0x10U;
                __Vdly__splitter__DOT__encoder__DOT__state = 4U;
            } else if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__encoder__DOT__state))) {
                vlSelf->__PVT__splitter__DOT__encoder__DOT__code = 0x10U;
                __Vdly__splitter__DOT__encoder__DOT__state = 4U;
            } else {
                __Vdly__splitter__DOT__encoder__DOT__state = 4U;
            }
        } else if ((2U & (IData)(vlSelf->__PVT__splitter__DOT__encoder__DOT__state))) {
            if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__encoder__DOT__state))) {
                if (vlSelf->__Vcellinp__splitter__DOT__encoder__start) {
                    __Vdly__splitter__DOT__encoder__DOT__remaining = 0U;
                    __Vdly__splitter__DOT__encoder__DOT__encoded = 0U;
                    __Vdly__splitter__DOT__encoder__DOT__final_scalar = 0U;
                    vlSelf->__PVT__splitter__DOT__encoder__DOT__code = 0U;
                    __Vdly__splitter__DOT__encoder__DOT__state = 1U;
                }
            } else if (((IData)(vlSelf->__PVT__splitter__DOT__encoder_valid) 
                        & ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                           & (6U == (IData)(vlSelf->__PVT__splitter__DOT__state))))) {
                if ((1U == (IData)(vlSelf->__PVT__splitter__DOT__encoder__DOT__remaining))) {
                    __Vdly__splitter__DOT__encoder__DOT__state 
                        = ((IData)(vlSelf->__PVT__splitter__DOT__encoder__DOT__final_scalar)
                            ? 3U : 1U);
                } else {
                    __Vdly__splitter__DOT__encoder__DOT__encoded 
                        = VL_SHIFTR_III(32,32,32, vlSelf->__PVT__splitter__DOT__encoder__DOT__encoded, 8U);
                    __Vdly__splitter__DOT__encoder__DOT__remaining 
                        = (7U & ((IData)(vlSelf->__PVT__splitter__DOT__encoder__DOT__remaining) 
                                 - (IData)(1U)));
                }
            }
        } else if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__encoder__DOT__state))) {
            if ((((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                  & (5U == (IData)(vlSelf->__PVT__splitter__DOT__state))) 
                 & (IData)(vlSelf->__PVT__splitter__DOT__encoder_ready))) {
                if (((0x10ffffU < vlSelf->__Vcellinp__splitter__DOT__classification__in_scalar) 
                     | ((0xd800U <= vlSelf->__Vcellinp__splitter__DOT__classification__in_scalar) 
                        & (0xdfffU >= vlSelf->__Vcellinp__splitter__DOT__classification__in_scalar)))) {
                    vlSelf->__PVT__splitter__DOT__encoder__DOT__code = 0x10U;
                    __Vdly__splitter__DOT__encoder__DOT__state = 4U;
                } else {
                    __Vdly__splitter__DOT__encoder__DOT__final_scalar 
                        = (((IData)(1U) + vlSelf->__PVT__splitter__DOT__scalar_index) 
                           == vlSelf->__PVT__splitter__DOT__scalar_count);
                    __Vdly__splitter__DOT__encoder__DOT__state = 2U;
                    if ((0x80U > vlSelf->__Vcellinp__splitter__DOT__classification__in_scalar)) {
                        __Vdly__splitter__DOT__encoder__DOT__encoded 
                            = (0xffU & vlSelf->__Vcellinp__splitter__DOT__classification__in_scalar);
                        __Vdly__splitter__DOT__encoder__DOT__remaining = 1U;
                    } else if ((0x800U > vlSelf->__Vcellinp__splitter__DOT__classification__in_scalar)) {
                        __Vdly__splitter__DOT__encoder__DOT__encoded 
                            = (0x80c0U | ((0x3f00U 
                                           & (vlSelf->__Vcellinp__splitter__DOT__classification__in_scalar 
                                              << 8U)) 
                                          | (0x1fU 
                                             & (vlSelf->__Vcellinp__splitter__DOT__classification__in_scalar 
                                                >> 6U))));
                        __Vdly__splitter__DOT__encoder__DOT__remaining = 2U;
                    } else if ((0x10000U > vlSelf->__Vcellinp__splitter__DOT__classification__in_scalar)) {
                        __Vdly__splitter__DOT__encoder__DOT__encoded 
                            = (0x8080e0U | ((0x3f0000U 
                                             & (vlSelf->__Vcellinp__splitter__DOT__classification__in_scalar 
                                                << 0x10U)) 
                                            | ((0x3f00U 
                                                & (vlSelf->__Vcellinp__splitter__DOT__classification__in_scalar 
                                                   << 2U)) 
                                               | (0xfU 
                                                  & (vlSelf->__Vcellinp__splitter__DOT__classification__in_scalar 
                                                     >> 0xcU)))));
                        __Vdly__splitter__DOT__encoder__DOT__remaining = 3U;
                    } else {
                        __Vdly__splitter__DOT__encoder__DOT__encoded 
                            = (0x808080f0U | ((0x3f000000U 
                                               & (vlSelf->__Vcellinp__splitter__DOT__classification__in_scalar 
                                                  << 0x18U)) 
                                              | ((0x3f0000U 
                                                  & (vlSelf->__Vcellinp__splitter__DOT__classification__in_scalar 
                                                     << 0xaU)) 
                                                 | ((0x3f00U 
                                                     & (vlSelf->__Vcellinp__splitter__DOT__classification__in_scalar 
                                                        >> 4U)) 
                                                    | (7U 
                                                       & (vlSelf->__Vcellinp__splitter__DOT__classification__in_scalar 
                                                          >> 0x12U))))));
                        __Vdly__splitter__DOT__encoder__DOT__remaining = 4U;
                    }
                }
            }
        } else if (vlSelf->__Vcellinp__splitter__DOT__encoder__start) {
            __Vdly__splitter__DOT__encoder__DOT__remaining = 0U;
            __Vdly__splitter__DOT__encoder__DOT__encoded = 0U;
            __Vdly__splitter__DOT__encoder__DOT__final_scalar = 0U;
            vlSelf->__PVT__splitter__DOT__encoder__DOT__code = 0U;
            __Vdly__splitter__DOT__encoder__DOT__state = 1U;
        }
        if ((8U & (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__state))) {
            if ((4U & (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__state))) {
                vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__failed = 1U;
                vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__code = 0x11U;
                __Vdly__splitter__DOT__edges__DOT__reader__DOT__state = 0xaU;
            } else if ((2U & (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__state))) {
                    vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__failed = 1U;
                    vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__code = 0x11U;
                    __Vdly__splitter__DOT__edges__DOT__reader__DOT__state = 0xaU;
                } else if (((IData)(vlSelf->__PVT__splitter__DOT__edge_valid) 
                            & ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                               & (0x10U == (IData)(vlSelf->__PVT__splitter__DOT__state))))) {
                    __Vdly__splitter__DOT__edges__DOT__reader__DOT__state = 0U;
                }
            } else if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__state))) {
                vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__result_data 
                    = (((~ (0xffffffffULL << (0x3fU 
                                              & VL_SHIFTL_III(6,32,32, (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__word_index), 5U)))) 
                        & vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__result_data) 
                       | ((QData)((IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__read_data)) 
                          << (0x3fU & VL_SHIFTL_III(6,32,32, (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__word_index), 5U))));
                if (vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__word_index) {
                    __Vdly__splitter__DOT__edges__DOT__reader__DOT__state = 0xaU;
                } else {
                    vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__word_index 
                        = (1U & ((IData)(1U) + (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__word_index)));
                    __Vtemp_20[0U] = 4U;
                    __Vtemp_20[1U] = 0U;
                    __Vtemp_20[2U] = 0U;
                    VL_ADD_W(3, __Vtemp_21, __Vtemp_20, vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__offset_value);
                    __Vdly__splitter__DOT__edges__DOT__reader__DOT__offset_value[0U] 
                        = __Vtemp_21[0U];
                    __Vdly__splitter__DOT__edges__DOT__reader__DOT__offset_value[1U] 
                        = __Vtemp_21[1U];
                    __Vdly__splitter__DOT__edges__DOT__reader__DOT__offset_value[2U] 
                        = (3U & __Vtemp_21[2U]);
                    __Vdly__splitter__DOT__edges__DOT__reader__DOT__state = 5U;
                }
            } else if ((((IData)(vlSelf->__PVT__splitter__DOT__edge_selected) 
                         & (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalized_specials__tbl_rsp_valid)) 
                        & (IData)(vlSelf->__PVT__splitter__DOT__edge_rsp_ready))) {
                if (vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer_rsp_error) {
                    vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__failed = 1U;
                    vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__code = 4U;
                    __Vdly__splitter__DOT__edges__DOT__reader__DOT__state = 0xaU;
                } else {
                    vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__read_data 
                        = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer_rsp_data;
                    __Vdly__splitter__DOT__edges__DOT__reader__DOT__state = 9U;
                }
            }
        } else if ((4U & (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__state))) {
            if ((2U & (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__state))) {
                    if (((IData)(vlSelf->__PVT__splitter__DOT__edge_req) 
                         & ((IData)(vlSelf->__PVT__splitter__DOT__edge_selected) 
                            & (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalized_specials__tbl_req_ready)))) {
                        __Vdly__splitter__DOT__edges__DOT__reader__DOT__state = 8U;
                    }
                } else if ((IData)(((0U != vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__request_address[2U]) 
                                    | VL_GTE_W(3, vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__request_address, vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__table_end)))) {
                    vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__failed = 1U;
                    vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__code = 0x11U;
                    __Vdly__splitter__DOT__edges__DOT__reader__DOT__state = 0xaU;
                } else {
                    __Vdly__splitter__DOT__edges__DOT__reader__DOT__state = 7U;
                }
            } else if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__state))) {
                VL_ADD_W(3, __Vtemp_23, vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__data_start, vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__offset_value);
                vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__request_address[0U] 
                    = __Vtemp_23[0U];
                vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__request_address[1U] 
                    = __Vtemp_23[1U];
                vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__request_address[2U] 
                    = (3U & __Vtemp_23[2U]);
                __Vdly__splitter__DOT__edges__DOT__reader__DOT__state = 6U;
            } else if ((IData)(((((0ULL != (3ULL & vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__base)) 
                                  | (0U != vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__data_start[2U])) 
                                 | (0U != vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__table_end[2U])) 
                                | ((0U == vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__count) 
                                   | (vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__index 
                                      >= vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__count))))) {
                vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__failed = 1U;
                vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__code = 0x11U;
                __Vdly__splitter__DOT__edges__DOT__reader__DOT__state = 0xaU;
            } else {
                __Vdly__splitter__DOT__edges__DOT__reader__DOT__state = 5U;
            }
        } else if ((2U & (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__state))) {
            if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__state))) {
                __Vtemp_25[0U] = vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__count;
                __Vtemp_25[1U] = 0U;
                __Vtemp_25[2U] = 0U;
                VL_SHIFTL_WWI(66,66,32, __Vtemp_26, __Vtemp_25, 3U);
                VL_ADD_W(3, __Vtemp_27, vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__data_start, __Vtemp_26);
                vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__table_end[0U] 
                    = __Vtemp_27[0U];
                vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__table_end[1U] 
                    = __Vtemp_27[1U];
                vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__table_end[2U] 
                    = (3U & __Vtemp_27[2U]);
                __Vdly__splitter__DOT__edges__DOT__reader__DOT__state = 4U;
            } else {
                __Vtemp_29[0U] = 0x20U;
                __Vtemp_29[1U] = 0U;
                __Vtemp_29[2U] = 0U;
                __Vtemp_30[0U] = (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__base);
                __Vtemp_30[1U] = (IData)((vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__base 
                                          >> 0x20U));
                __Vtemp_30[2U] = 0U;
                VL_ADD_W(3, __Vtemp_31, __Vtemp_29, __Vtemp_30);
                vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__data_start[0U] 
                    = __Vtemp_31[0U];
                vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__data_start[1U] 
                    = __Vtemp_31[1U];
                vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__data_start[2U] 
                    = (3U & __Vtemp_31[2U]);
                __Vdly__splitter__DOT__edges__DOT__reader__DOT__state = 3U;
            }
        } else if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__state))) {
            __Vtemp_33[0U] = vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__index;
            __Vtemp_33[1U] = 0U;
            __Vtemp_33[2U] = 0U;
            VL_SHIFTL_WWI(66,66,32, __Vtemp_34, __Vtemp_33, 3U);
            __Vdly__splitter__DOT__edges__DOT__reader__DOT__offset_value[0U] 
                = __Vtemp_34[0U];
            __Vdly__splitter__DOT__edges__DOT__reader__DOT__offset_value[1U] 
                = __Vtemp_34[1U];
            __Vdly__splitter__DOT__edges__DOT__reader__DOT__offset_value[2U] 
                = (3U & __Vtemp_34[2U]);
            __Vdly__splitter__DOT__edges__DOT__reader__DOT__state = 2U;
        } else if ((((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                     & (0xfU == (IData)(vlSelf->__PVT__splitter__DOT__state))) 
                    & (IData)(vlSelf->__PVT__splitter__DOT__edge_ready))) {
            vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__word_index = 0U;
            vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__base 
                = (((QData)((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__table_bases[0xdU])) 
                    << 0x20U) | (QData)((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__table_bases[0xcU])));
            vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__count 
                = vlSymsp->TOP.bench__DOT__dut__DOT__committed_counts[6U];
            vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__index 
                = (vlSelf->__PVT__splitter__DOT__edge_first 
                   + vlSelf->__PVT__splitter__DOT__edge_cursor);
            vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__result_data = 0ULL;
            vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__failed = 0U;
            vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__code = 0U;
            __Vdly__splitter__DOT__edges__DOT__reader__DOT__state = 1U;
        }
        if ((8U & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__state))) {
            vlSelf->__PVT__splitter__DOT__classification__DOT__failed = 1U;
            vlSelf->__PVT__splitter__DOT__classification__DOT__code = 0x12U;
            __Vdly__splitter__DOT__classification__DOT__state = 6U;
        } else if ((4U & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__state))) {
            if ((2U & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__state))) {
                    vlSelf->__PVT__splitter__DOT__classification__DOT__failed = 1U;
                    vlSelf->__PVT__splitter__DOT__classification__DOT__code = 0x12U;
                    __Vdly__splitter__DOT__classification__DOT__state = 6U;
                } else if (((IData)(vlSelf->__PVT__splitter__DOT__class_valid) 
                            & ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                               & (3U == (IData)(vlSelf->__PVT__splitter__DOT__state))))) {
                    __Vdly__splitter__DOT__classification__DOT__state = 0U;
                }
            } else if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__state))) {
                if ((((((vlSelf->__PVT__splitter__DOT__classification__DOT__first_scalar 
                         > vlSelf->__PVT__splitter__DOT__classification__DOT__last_scalar) 
                        | (0x10ffffU < vlSelf->__PVT__splitter__DOT__classification__DOT__last_scalar)) 
                       | ((0xdfffU >= vlSelf->__PVT__splitter__DOT__classification__DOT__first_scalar) 
                          & (0xd800U <= vlSelf->__PVT__splitter__DOT__classification__DOT__last_scalar))) 
                      | (vlSelf->__PVT__splitter__DOT__classification__DOT__class_value 
                         >= vlSelf->__PVT__splitter__DOT__classification__DOT__class_count)) 
                     | (0U != (vlSelf->__PVT__splitter__DOT__classification__DOT__property_value 
                               >> 0xaU)))) {
                    vlSelf->__PVT__splitter__DOT__classification__DOT__failed = 1U;
                    vlSelf->__PVT__splitter__DOT__classification__DOT__code = 0x12U;
                    __Vdly__splitter__DOT__classification__DOT__state = 6U;
                } else if ((vlSelf->__PVT__splitter__DOT__classification__DOT__scalar 
                            < vlSelf->__PVT__splitter__DOT__classification__DOT__first_scalar)) {
                    __Vdly__splitter__DOT__classification__DOT__high_index 
                        = vlSelf->__PVT__splitter__DOT__classification__DOT__middle;
                    __Vdly__splitter__DOT__classification__DOT__state = 2U;
                } else if ((vlSelf->__PVT__splitter__DOT__classification__DOT__scalar 
                            > vlSelf->__PVT__splitter__DOT__classification__DOT__last_scalar)) {
                    __Vdly__splitter__DOT__classification__DOT__low_index 
                        = ((IData)(1U) + vlSelf->__PVT__splitter__DOT__classification__DOT__middle);
                    __Vdly__splitter__DOT__classification__DOT__state = 2U;
                } else {
                    __Vdly__splitter__DOT__classification__DOT__state = 6U;
                }
            } else if (vlSelf->__PVT__splitter__DOT__classification__DOT__reader_valid) {
                if (((IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__reader_valid) 
                     & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__failed))) {
                    vlSelf->__PVT__splitter__DOT__classification__DOT__failed = 1U;
                    vlSelf->__PVT__splitter__DOT__classification__DOT__code 
                        = ((IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__reader_valid)
                            ? (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__code)
                            : 0U);
                    __Vdly__splitter__DOT__classification__DOT__state = 6U;
                } else {
                    vlSelf->__PVT__splitter__DOT__classification__DOT__first_scalar 
                        = vlSelf->__PVT__splitter__DOT__classification__DOT__reader_data[0U];
                    vlSelf->__PVT__splitter__DOT__classification__DOT__last_scalar 
                        = vlSelf->__PVT__splitter__DOT__classification__DOT__reader_data[1U];
                    vlSelf->__PVT__splitter__DOT__classification__DOT__class_value 
                        = vlSelf->__PVT__splitter__DOT__classification__DOT__reader_data[2U];
                    vlSelf->__PVT__splitter__DOT__classification__DOT__property_value 
                        = vlSelf->__PVT__splitter__DOT__classification__DOT__reader_data[3U];
                    __Vdly__splitter__DOT__classification__DOT__state = 5U;
                }
            }
        } else if ((2U & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__state))) {
            if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__state))) {
                if (vlSelf->__PVT__splitter__DOT__classification__DOT__reader_ready) {
                    __Vdly__splitter__DOT__classification__DOT__state = 4U;
                }
            } else if ((vlSelf->__PVT__splitter__DOT__classification__DOT__low_index 
                        >= vlSelf->__PVT__splitter__DOT__classification__DOT__high_index)) {
                vlSelf->__PVT__splitter__DOT__classification__DOT__failed = 1U;
                vlSelf->__PVT__splitter__DOT__classification__DOT__code = 0x12U;
                __Vdly__splitter__DOT__classification__DOT__state = 6U;
            } else {
                __Vdly__splitter__DOT__classification__DOT__middle 
                    = (vlSelf->__PVT__splitter__DOT__classification__DOT__low_index 
                       + VL_SHIFTR_III(32,32,32, (vlSelf->__PVT__splitter__DOT__classification__DOT__high_index 
                                                  - vlSelf->__PVT__splitter__DOT__classification__DOT__low_index), 1U));
                __Vdly__splitter__DOT__classification__DOT__state = 3U;
            }
        } else if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__state))) {
            if (((0x10ffffU < vlSelf->__PVT__splitter__DOT__classification__DOT__scalar) 
                 | ((0xd800U <= vlSelf->__PVT__splitter__DOT__classification__DOT__scalar) 
                    & (0xdfffU >= vlSelf->__PVT__splitter__DOT__classification__DOT__scalar)))) {
                vlSelf->__PVT__splitter__DOT__classification__DOT__failed = 1U;
                vlSelf->__PVT__splitter__DOT__classification__DOT__code = 0x10U;
                __Vdly__splitter__DOT__classification__DOT__state = 6U;
            } else if ((1U & ((((~ (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__admitted)) 
                                | (0U == vlSelf->__PVT__splitter__DOT__classification__DOT__range_count)) 
                               | (0U == vlSelf->__PVT__splitter__DOT__classification__DOT__class_count)) 
                              | (0U != (3U & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__base)))))) {
                vlSelf->__PVT__splitter__DOT__classification__DOT__failed = 1U;
                vlSelf->__PVT__splitter__DOT__classification__DOT__code = 6U;
                __Vdly__splitter__DOT__classification__DOT__state = 6U;
            } else {
                __Vdly__splitter__DOT__classification__DOT__state = 2U;
            }
        } else if ((((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                     & (2U == (IData)(vlSelf->__PVT__splitter__DOT__state))) 
                    & (IData)(vlSelf->__PVT__splitter__DOT__class_ready))) {
            vlSelf->__PVT__splitter__DOT__classification__DOT__admitted 
                = vlSymsp->TOP.bench__DOT__boot_done;
            __Vdly__splitter__DOT__classification__DOT__base 
                = (((QData)((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__table_bases[0xfU])) 
                    << 0x20U) | (QData)((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__table_bases[0xeU])));
            __Vdly__splitter__DOT__classification__DOT__range_count 
                = vlSymsp->TOP.bench__DOT__dut__DOT__committed_counts[7U];
            vlSelf->__PVT__splitter__DOT__classification__DOT__class_count 
                = vlSymsp->TOP.bench__DOT__dut__DOT__committed_metadata[9U];
            vlSelf->__PVT__splitter__DOT__classification__DOT__scalar 
                = vlSelf->__Vcellinp__splitter__DOT__classification__in_scalar;
            __Vdly__splitter__DOT__classification__DOT__low_index = 0U;
            __Vdly__splitter__DOT__classification__DOT__high_index 
                = vlSymsp->TOP.bench__DOT__dut__DOT__committed_counts[7U];
            vlSelf->__PVT__splitter__DOT__classification__DOT__failed = 0U;
            vlSelf->__PVT__splitter__DOT__classification__DOT__code = 0U;
            vlSelf->__PVT__splitter__DOT__classification__DOT__class_value = 0U;
            vlSelf->__PVT__splitter__DOT__classification__DOT__property_value = 0U;
            __Vdly__splitter__DOT__classification__DOT__state = 1U;
        }
        if ((8U & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
            if ((4U & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
                vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__failed = 1U;
                vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__code = 0x11U;
                __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 0xaU;
            } else if ((2U & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
                    vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__failed = 1U;
                    vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__code = 0x11U;
                    __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 0xaU;
                } else if (((IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__reader_valid) 
                            & ((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                               & (4U == (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__state))))) {
                    __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 0U;
                }
            } else if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
                VL_ASSIGNSEL_WI(128,32,(0x7fU & VL_SHIFTL_III(7,32,32, (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__word_index), 5U)), vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data, vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__read_data);
                if ((3U == (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__word_index))) {
                    __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 0xaU;
                } else {
                    vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__word_index 
                        = (3U & ((IData)(1U) + (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__word_index)));
                    __Vtemp_37[0U] = 4U;
                    __Vtemp_37[1U] = 0U;
                    __Vtemp_37[2U] = 0U;
                    VL_ADD_W(3, __Vtemp_38, __Vtemp_37, vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value);
                    __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[0U] 
                        = __Vtemp_38[0U];
                    __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[1U] 
                        = __Vtemp_38[1U];
                    __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[2U] 
                        = (3U & __Vtemp_38[2U]);
                    __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 5U;
                }
            } else if ((((IData)(vlSelf->__PVT__splitter__DOT__classify_selected) 
                         & (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalized_specials__tbl_rsp_valid)) 
                        & (IData)(vlSelf->__PVT__splitter__DOT__class_rsp_ready))) {
                if (vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer_rsp_error) {
                    vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__failed = 1U;
                    vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__code = 4U;
                    __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 0xaU;
                } else {
                    vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__read_data 
                        = vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer_rsp_data;
                    __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 9U;
                }
            }
        } else if ((4U & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
            if ((2U & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
                    if (((IData)(vlSelf->__PVT__splitter__DOT__class_req) 
                         & ((IData)(vlSelf->__PVT__splitter__DOT__classify_selected) 
                            & (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalized_specials__tbl_req_ready)))) {
                        __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 8U;
                    }
                } else if ((IData)(((0U != vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__request_address[2U]) 
                                    | VL_GTE_W(3, vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__request_address, vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__table_end)))) {
                    vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__failed = 1U;
                    vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__code = 0x11U;
                    __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 0xaU;
                } else {
                    __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 7U;
                }
            } else if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
                VL_ADD_W(3, __Vtemp_40, vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__data_start, vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value);
                vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__request_address[0U] 
                    = __Vtemp_40[0U];
                vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__request_address[1U] 
                    = __Vtemp_40[1U];
                vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__request_address[2U] 
                    = (3U & __Vtemp_40[2U]);
                __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 6U;
            } else if ((IData)(((((0ULL != (3ULL & vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__base)) 
                                  | (0U != vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__data_start[2U])) 
                                 | (0U != vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__table_end[2U])) 
                                | ((0U == vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__count) 
                                   | (vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__index 
                                      >= vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__count))))) {
                vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__failed = 1U;
                vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__code = 0x11U;
                __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 0xaU;
            } else {
                __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 5U;
            }
        } else if ((2U & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
            if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
                __Vtemp_42[0U] = vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__count;
                __Vtemp_42[1U] = 0U;
                __Vtemp_42[2U] = 0U;
                VL_SHIFTL_WWI(66,66,32, __Vtemp_43, __Vtemp_42, 4U);
                VL_ADD_W(3, __Vtemp_44, vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__data_start, __Vtemp_43);
                vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__table_end[0U] 
                    = __Vtemp_44[0U];
                vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__table_end[1U] 
                    = __Vtemp_44[1U];
                vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__table_end[2U] 
                    = (3U & __Vtemp_44[2U]);
                __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 4U;
            } else {
                __Vtemp_46[0U] = 0x20U;
                __Vtemp_46[1U] = 0U;
                __Vtemp_46[2U] = 0U;
                __Vtemp_47[0U] = (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__base);
                __Vtemp_47[1U] = (IData)((vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__base 
                                          >> 0x20U));
                __Vtemp_47[2U] = 0U;
                VL_ADD_W(3, __Vtemp_48, __Vtemp_46, __Vtemp_47);
                vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__data_start[0U] 
                    = __Vtemp_48[0U];
                vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__data_start[1U] 
                    = __Vtemp_48[1U];
                vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__data_start[2U] 
                    = (3U & __Vtemp_48[2U]);
                __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 3U;
            }
        } else if ((1U & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state))) {
            __Vtemp_50[0U] = vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__index;
            __Vtemp_50[1U] = 0U;
            __Vtemp_50[2U] = 0U;
            VL_SHIFTL_WWI(66,66,32, __Vtemp_51, __Vtemp_50, 4U);
            __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[0U] 
                = __Vtemp_51[0U];
            __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[1U] 
                = __Vtemp_51[1U];
            __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[2U] 
                = (3U & __Vtemp_51[2U]);
            __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 2U;
        } else if ((((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__client_rst_n) 
                     & (3U == (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__state))) 
                    & (IData)(vlSelf->__PVT__splitter__DOT__classification__DOT__reader_ready))) {
            vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__word_index = 0U;
            vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__base 
                = vlSelf->__PVT__splitter__DOT__classification__DOT__base;
            vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__count 
                = vlSelf->__PVT__splitter__DOT__classification__DOT__range_count;
            vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__index 
                = vlSelf->__PVT__splitter__DOT__classification__DOT__middle;
            vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[0U] = 0U;
            vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[1U] = 0U;
            vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[2U] = 0U;
            vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[3U] = 0U;
            vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__failed = 0U;
            vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__code = 0U;
            __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 1U;
        }
    } else {
        vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__word_index = 0U;
        __Vdly__splitter__DOT__records__DOT__reader__DOT__offset_value[0U] = 0U;
        __Vdly__splitter__DOT__records__DOT__reader__DOT__offset_value[1U] = 0U;
        __Vdly__splitter__DOT__records__DOT__reader__DOT__offset_value[2U] = 0U;
        __Vdly__splitter__DOT__records__DOT__reader__DOT__state = 0U;
        vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__base = 0ULL;
        vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__count = 0U;
        vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__index = 0U;
        vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__data_start[0U] = 0U;
        vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__data_start[1U] = 0U;
        vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__data_start[2U] = 0U;
        vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__table_end[0U] = 0U;
        vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__table_end[1U] = 0U;
        vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__table_end[2U] = 0U;
        vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__request_address[0U] = 0U;
        vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__request_address[1U] = 0U;
        vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__request_address[2U] = 0U;
        vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__result_data[0U] = 0U;
        vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__result_data[1U] = 0U;
        vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__result_data[2U] = 0U;
        vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__result_data[3U] = 0U;
        vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__read_data = 0U;
        vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__failed = 0U;
        vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__code = 0U;
        __Vdly__splitter__DOT__cursor = 0U;
        __Vdly__splitter__DOT__edge_cursor = 0U;
        __Vdly__splitter__DOT__state = 0U;
        __Vdly__splitter__DOT__scalar_count = 0U;
        __Vdly__splitter__DOT__scalar_index = 0U;
        __Vdly__splitter__DOT__byte_count = 0U;
        __Vdly__splitter__DOT__scan_index = 0U;
        __Vdly__splitter__DOT__plan_count = 0U;
        __Vdly__splitter__DOT__output_index = 0U;
        __Vdly__splitter__DOT__encoded_remaining = 0U;
        vlSelf->__PVT__splitter__DOT__node_index = 0U;
        __Vdly__splitter__DOT__edge_first = 0U;
        vlSelf->__PVT__splitter__DOT__edge_count = 0U;
        vlSelf->__PVT__splitter__DOT__terminal_index = 0U;
        vlSelf->__PVT__splitter__DOT__best_end = 0U;
        vlSelf->__PVT__splitter__DOT__best_token = 0U;
        vlSelf->__PVT__splitter__DOT__best_flags = 0U;
        vlSelf->__PVT__splitter__DOT__best_record = 0U;
        vlSelf->__PVT__splitter__DOT__best_valid = 0U;
        vlSelf->__PVT__splitter__DOT__phase = 0U;
        vlSelf->__PVT__splitter__DOT__node_record[0U] = 0U;
        vlSelf->__PVT__splitter__DOT__node_record[1U] = 0U;
        vlSelf->__PVT__splitter__DOT__node_record[2U] = 0U;
        vlSelf->__PVT__splitter__DOT__node_record[3U] = 0U;
        vlSelf->__PVT__splitter__DOT__special_record[0U] = 0U;
        vlSelf->__PVT__splitter__DOT__special_record[1U] = 0U;
        vlSelf->__PVT__splitter__DOT__special_record[2U] = 0U;
        vlSelf->__PVT__splitter__DOT__special_record[3U] = 0U;
        vlSelf->__PVT__splitter__DOT__edge_record = 0ULL;
        vlSelf->__PVT__splitter__DOT__code = 0U;
        vlSelf->__PVT__splitter__DOT__output_value = 0U;
        vlSelf->__PVT__splitter__DOT__output_special = 0U;
        vlSelf->__PVT__splitter__DOT__output_boundary = 0U;
        __Vdly__splitter__DOT__output_last = 0U;
        __Vdly__splitter__DOT__encoder__DOT__state = 0U;
        __Vdly__splitter__DOT__encoder__DOT__remaining = 0U;
        __Vdly__splitter__DOT__encoder__DOT__encoded = 0U;
        __Vdly__splitter__DOT__encoder__DOT__final_scalar = 0U;
        vlSelf->__PVT__splitter__DOT__encoder__DOT__code = 0U;
        vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__word_index = 0U;
        __Vdly__splitter__DOT__edges__DOT__reader__DOT__offset_value[0U] = 0U;
        __Vdly__splitter__DOT__edges__DOT__reader__DOT__offset_value[1U] = 0U;
        __Vdly__splitter__DOT__edges__DOT__reader__DOT__offset_value[2U] = 0U;
        __Vdly__splitter__DOT__edges__DOT__reader__DOT__state = 0U;
        vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__base = 0ULL;
        vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__count = 0U;
        vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__index = 0U;
        vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__data_start[0U] = 0U;
        vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__data_start[1U] = 0U;
        vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__data_start[2U] = 0U;
        vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__table_end[0U] = 0U;
        vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__table_end[1U] = 0U;
        vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__table_end[2U] = 0U;
        vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__request_address[0U] = 0U;
        vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__request_address[1U] = 0U;
        vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__request_address[2U] = 0U;
        vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__result_data = 0ULL;
        vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__read_data = 0U;
        vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__failed = 0U;
        vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__code = 0U;
        __Vdly__splitter__DOT__classification__DOT__state = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__admitted = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__failed = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__code = 0U;
        __Vdly__splitter__DOT__classification__DOT__base = 0ULL;
        vlSelf->__PVT__splitter__DOT__classification__DOT__scalar = 0U;
        __Vdly__splitter__DOT__classification__DOT__range_count = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__class_count = 0U;
        __Vdly__splitter__DOT__classification__DOT__low_index = 0U;
        __Vdly__splitter__DOT__classification__DOT__high_index = 0U;
        __Vdly__splitter__DOT__classification__DOT__middle = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__first_scalar = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__last_scalar = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__class_value = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__property_value = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__word_index = 0U;
        __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[0U] = 0U;
        __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[1U] = 0U;
        __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[2U] = 0U;
        __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__base = 0ULL;
        vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__count = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__index = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__data_start[0U] = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__data_start[1U] = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__data_start[2U] = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__table_end[0U] = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__table_end[1U] = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__table_end[2U] = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__request_address[0U] = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__request_address[1U] = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__request_address[2U] = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[0U] = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[1U] = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[2U] = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[3U] = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__read_data = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__failed = 0U;
        vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__code = 0U;
    }
    vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__offset_value[0U] 
        = __Vdly__splitter__DOT__records__DOT__reader__DOT__offset_value[0U];
    vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__offset_value[1U] 
        = __Vdly__splitter__DOT__records__DOT__reader__DOT__offset_value[1U];
    vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__offset_value[2U] 
        = __Vdly__splitter__DOT__records__DOT__reader__DOT__offset_value[2U];
    vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__state 
        = __Vdly__splitter__DOT__records__DOT__reader__DOT__state;
    vlSelf->__PVT__splitter__DOT__byte_count = __Vdly__splitter__DOT__byte_count;
    vlSelf->__PVT__splitter__DOT__plan_count = __Vdly__splitter__DOT__plan_count;
    vlSelf->__PVT__splitter__DOT__output_index = __Vdly__splitter__DOT__output_index;
    vlSelf->__PVT__splitter__DOT__output_last = __Vdly__splitter__DOT__output_last;
    vlSelf->__PVT__splitter__DOT__encoded_remaining 
        = __Vdly__splitter__DOT__encoded_remaining;
    if (__Vdlyvset__splitter__DOT__scalar_starts__v0) {
        vlSelf->__PVT__splitter__DOT__scalar_starts[__Vdlyvdim0__splitter__DOT__scalar_starts__v0] 
            = __Vdlyvval__splitter__DOT__scalar_starts__v0;
    }
    if (__Vdlyvset__splitter__DOT__plan_value__v0) {
        vlSelf->__PVT__splitter__DOT__plan_value[__Vdlyvdim0__splitter__DOT__plan_value__v0] 
            = __Vdlyvval__splitter__DOT__plan_value__v0;
    }
    if (__Vdlyvset__splitter__DOT__plan_value__v1) {
        vlSelf->__PVT__splitter__DOT__plan_value[__Vdlyvdim0__splitter__DOT__plan_value__v1] 
            = __Vdlyvval__splitter__DOT__plan_value__v1;
    }
    if (__Vdlyvset__splitter__DOT__scalars__v0) {
        vlSelf->__PVT__splitter__DOT__scalars[__Vdlyvdim0__splitter__DOT__scalars__v0] 
            = __Vdlyvval__splitter__DOT__scalars__v0;
    }
    vlSelf->__PVT__splitter__DOT__scan_index = __Vdly__splitter__DOT__scan_index;
    if (__Vdlyvset__splitter__DOT__plan_special__v0) {
        vlSelf->__PVT__splitter__DOT__plan_special[__Vdlyvdim0__splitter__DOT__plan_special__v0] = 0U;
        vlSelf->__PVT__splitter__DOT__plan_space[__Vdlyvdim0__splitter__DOT__plan_space__v0] 
            = __Vdlyvval__splitter__DOT__plan_space__v0;
    }
    if (__Vdlyvset__splitter__DOT__plan_special__v1) {
        vlSelf->__PVT__splitter__DOT__plan_special[__Vdlyvdim0__splitter__DOT__plan_special__v1] = 1U;
        vlSelf->__PVT__splitter__DOT__plan_space[__Vdlyvdim0__splitter__DOT__plan_space__v1] = 0U;
    }
    if (__Vdlyvset__splitter__DOT__properties__v0) {
        vlSelf->__PVT__splitter__DOT__properties[__Vdlyvdim0__splitter__DOT__properties__v0] 
            = __Vdlyvval__splitter__DOT__properties__v0;
    }
    if (__Vdlyvset__splitter__DOT__bytes_memory__v0) {
        vlSelf->__PVT__splitter__DOT__bytes_memory[__Vdlyvdim0__splitter__DOT__bytes_memory__v0] 
            = __Vdlyvval__splitter__DOT__bytes_memory__v0;
        vlSelf->__PVT__splitter__DOT__byte_ends[__Vdlyvdim0__splitter__DOT__byte_ends__v0] 
            = __Vdlyvval__splitter__DOT__byte_ends__v0;
    }
    vlSelf->__PVT__splitter__DOT__cursor = __Vdly__splitter__DOT__cursor;
    vlSelf->__PVT__splitter__DOT__special_flags = vlSelf->__PVT__splitter__DOT__special_record[1U];
    __VdfgTmp_hb6edd8f3__0 = vlSelf->__PVT__splitter__DOT__byte_ends
        [(0xfU & (vlSelf->__PVT__splitter__DOT__cursor 
                  - (IData)(1U)))];
    vlSelf->__PVT__splitter__DOT__terminal_end = ((0U 
                                                   == vlSelf->__PVT__splitter__DOT__cursor)
                                                   ? 0U
                                                   : __VdfgTmp_hb6edd8f3__0);
    vlSelf->__PVT__splitter__DOT__encoder__DOT__remaining 
        = __Vdly__splitter__DOT__encoder__DOT__remaining;
    vlSelf->__PVT__splitter__DOT__encoder__DOT__final_scalar 
        = __Vdly__splitter__DOT__encoder__DOT__final_scalar;
    vlSelf->__PVT__splitter__DOT__encoder__DOT__encoded 
        = __Vdly__splitter__DOT__encoder__DOT__encoded;
    vlSelf->__PVT__splitter__DOT__scalar_index = __Vdly__splitter__DOT__scalar_index;
    vlSelf->__PVT__splitter__DOT__encoder__DOT__state 
        = __Vdly__splitter__DOT__encoder__DOT__state;
    vlSelf->__PVT__splitter__DOT__scalar_count = __Vdly__splitter__DOT__scalar_count;
    vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__offset_value[0U] 
        = __Vdly__splitter__DOT__edges__DOT__reader__DOT__offset_value[0U];
    vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__offset_value[1U] 
        = __Vdly__splitter__DOT__edges__DOT__reader__DOT__offset_value[1U];
    vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__offset_value[2U] 
        = __Vdly__splitter__DOT__edges__DOT__reader__DOT__offset_value[2U];
    vlSelf->__PVT__splitter__DOT__edge_cursor = __Vdly__splitter__DOT__edge_cursor;
    vlSelf->__PVT__splitter__DOT__edge_first = __Vdly__splitter__DOT__edge_first;
    vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__state 
        = __Vdly__splitter__DOT__edges__DOT__reader__DOT__state;
    vlSelf->__PVT__splitter__DOT__classification__DOT__high_index 
        = __Vdly__splitter__DOT__classification__DOT__high_index;
    vlSelf->__PVT__splitter__DOT__classification__DOT__low_index 
        = __Vdly__splitter__DOT__classification__DOT__low_index;
    vlSelf->__PVT__splitter__DOT__state = __Vdly__splitter__DOT__state;
    vlSelf->__Vcellinp__splitter__DOT__classification__in_scalar 
        = vlSelf->__PVT__splitter__DOT__scalars[(0xfU 
                                                 & vlSelf->__PVT__splitter__DOT__scalar_index)];
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
    vlSelf->__PVT__splitter__DOT__edge_end = (0x1ffffffffULL 
                                              & ((QData)((IData)(vlSelf->__PVT__splitter__DOT__edge_first)) 
                                                 + (QData)((IData)(vlSelf->__PVT__splitter__DOT__edge_count))));
    vlSelf->__PVT__splitter__DOT__special_selected 
        = ((0xbU == (IData)(vlSelf->__PVT__splitter__DOT__state)) 
           | (0xcU == (IData)(vlSelf->__PVT__splitter__DOT__state)));
    vlSelf->__PVT__splitter__DOT__edge_selected = (
                                                   (0xfU 
                                                    == (IData)(vlSelf->__PVT__splitter__DOT__state)) 
                                                   | (0x10U 
                                                      == (IData)(vlSelf->__PVT__splitter__DOT__state)));
    vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[0U] 
        = __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[0U];
    vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[1U] 
        = __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[1U];
    vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[2U] 
        = __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value[2U];
    vlSelf->__PVT__splitter__DOT__classification__DOT__base 
        = __Vdly__splitter__DOT__classification__DOT__base;
    vlSelf->__PVT__splitter__DOT__classification__DOT__range_count 
        = __Vdly__splitter__DOT__classification__DOT__range_count;
    vlSelf->__PVT__splitter__DOT__classification__DOT__middle 
        = __Vdly__splitter__DOT__classification__DOT__middle;
    vlSelf->__PVT__splitter__DOT__classification__DOT__state 
        = __Vdly__splitter__DOT__classification__DOT__state;
    vlSelf->__PVT__splitter__DOT__classify_selected 
        = ((2U == (IData)(vlSelf->__PVT__splitter__DOT__state)) 
           | (3U == (IData)(vlSelf->__PVT__splitter__DOT__state)));
    vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state 
        = __Vdly__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state;
    vlSelf->__VdfgTmp_hed1c005a__0 = (1U & ((~ (IData)(vlSelf->__PVT__splitter__DOT__classify_selected)) 
                                            & (~ (IData)(vlSelf->__PVT__splitter__DOT__edge_selected))));
}
