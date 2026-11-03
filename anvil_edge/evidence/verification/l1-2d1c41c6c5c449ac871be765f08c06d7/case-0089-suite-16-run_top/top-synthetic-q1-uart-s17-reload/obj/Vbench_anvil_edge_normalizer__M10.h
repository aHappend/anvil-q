// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design internal header
// See Vbench.h for the primary calling header

#ifndef VERILATED_VBENCH_ANVIL_EDGE_NORMALIZER__M10_H_
#define VERILATED_VBENCH_ANVIL_EDGE_NORMALIZER__M10_H_  // guard

#include "verilated.h"
#include "verilated_timing.h"


class Vbench__Syms;

class alignas(VL_CACHE_LINE_BYTES) Vbench_anvil_edge_normalizer__M10 final : public VerilatedModule {
  public:

    // DESIGN SPECIFIC STATE
    // Anonymous structures to workaround compiler member-count bugs
    struct {
        VL_IN8(clk,0,0);
        VL_IN8(rst_n,0,0);
        VL_IN8(start,0,0);
        VL_IN8(config_valid,0,0);
        VL_IN8(in_valid,0,0);
        VL_OUT8(in_ready,0,0);
        VL_IN8(in_last,0,0);
        VL_OUT8(out_valid,0,0);
        VL_IN8(out_ready,0,0);
        VL_OUT8(out_last,0,0);
        VL_OUT8(__PVT__busy,0,0);
        VL_OUT8(__PVT__done,0,0);
        VL_OUT8(error,0,0);
        VL_OUT8(error_code,7,0);
        VL_OUT8(tbl_req_valid,0,0);
        VL_IN8(tbl_req_ready,0,0);
        VL_IN8(tbl_rsp_valid,0,0);
        VL_OUT8(tbl_rsp_ready,0,0);
        VL_IN8(tbl_rsp_error,0,0);
        CData/*5:0*/ __PVT__normalizer__DOT__state;
        CData/*0:0*/ __PVT__normalizer__DOT__input_last;
        CData/*1:0*/ __PVT__normalizer__DOT__append_source;
        CData/*1:0*/ __PVT__normalizer__DOT__hangul_part;
        CData/*7:0*/ __PVT__normalizer__DOT__append_ccc;
        CData/*7:0*/ __PVT__normalizer__DOT__previous_ccc;
        CData/*0:0*/ __PVT__normalizer__DOT__reading_composition;
        CData/*7:0*/ __PVT__normalizer__DOT__current_ccc;
        CData/*7:0*/ __PVT__normalizer__DOT__last_ccc;
        CData/*0:0*/ __PVT__normalizer__DOT__starter_valid;
        CData/*7:0*/ __PVT__normalizer__DOT__code;
        CData/*0:0*/ __PVT__normalizer__DOT__classify_selected;
        CData/*0:0*/ __PVT__normalizer__DOT__pool_selected;
        CData/*0:0*/ __PVT__normalizer__DOT__record_ready;
        CData/*0:0*/ __PVT__normalizer__DOT__record_valid;
        CData/*0:0*/ __PVT__normalizer__DOT__record_tbl_valid;
        CData/*0:0*/ __PVT__normalizer__DOT__record_tbl_ready;
        CData/*0:0*/ __PVT__normalizer__DOT__pool_ready;
        CData/*0:0*/ __PVT__normalizer__DOT__pool_valid;
        CData/*0:0*/ __PVT__normalizer__DOT__pool_tbl_valid;
        CData/*0:0*/ __PVT__normalizer__DOT__pool_tbl_ready;
        CData/*0:0*/ __PVT__normalizer__DOT__class_ready;
        CData/*0:0*/ __PVT__normalizer__DOT__class_valid;
        CData/*0:0*/ __PVT__normalizer__DOT__class_tbl_valid;
        CData/*0:0*/ __PVT__normalizer__DOT__class_tbl_ready;
        CData/*0:0*/ __PVT__normalizer__DOT__divider_ready;
        CData/*0:0*/ __PVT__normalizer__DOT__divider_valid;
        CData/*0:0*/ __PVT__normalizer__DOT__divider_zero;
        CData/*0:0*/ __PVT__normalizer__DOT__record_scalar_valid;
        CData/*0:0*/ __PVT__normalizer__DOT__composition_before;
        CData/*0:0*/ __PVT__normalizer__DOT__composition_equal;
        CData/*0:0*/ __VdfgTmp_h0a1e14da__0;
        CData/*3:0*/ __PVT__normalizer__DOT__records__DOT__reader__DOT__state;
        CData/*1:0*/ __PVT__normalizer__DOT__records__DOT__reader__DOT__word_index;
        CData/*0:0*/ __PVT__normalizer__DOT__records__DOT__reader__DOT__failed;
        CData/*7:0*/ __PVT__normalizer__DOT__records__DOT__reader__DOT__code;
        CData/*3:0*/ __PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__state;
        CData/*0:0*/ __PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__word_index;
        CData/*0:0*/ __PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__failed;
        CData/*7:0*/ __PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__code;
        CData/*3:0*/ __PVT__normalizer__DOT__classification__DOT__state;
        CData/*0:0*/ __PVT__normalizer__DOT__classification__DOT__admitted;
        CData/*0:0*/ __PVT__normalizer__DOT__classification__DOT__failed;
        CData/*7:0*/ __PVT__normalizer__DOT__classification__DOT__code;
        CData/*0:0*/ __PVT__normalizer__DOT__classification__DOT__reader_ready;
    };
    struct {
        CData/*0:0*/ __PVT__normalizer__DOT__classification__DOT__reader_valid;
        CData/*3:0*/ __PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__state;
        CData/*1:0*/ __PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__word_index;
        CData/*0:0*/ __PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__failed;
        CData/*7:0*/ __PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__code;
        CData/*1:0*/ __PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__state;
        CData/*5:0*/ __PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__iterations;
        CData/*0:0*/ __PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__zero_divisor;
        CData/*0:0*/ __PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__subtract;
        VL_IN(cfg_normalization,31,0);
        VL_IN(cfg_range_count,31,0);
        VL_IN(cfg_class_count,31,0);
        VL_IN(cfg_decomposition_count,31,0);
        VL_IN(cfg_scalar_pool_count,31,0);
        VL_IN(cfg_composition_count,31,0);
        VL_IN(in_scalar,31,0);
        VL_OUT(out_scalar,31,0);
        VL_IN(tbl_rsp_data,31,0);
        IData/*31:0*/ __PVT__normalizer__DOT__mode;
        IData/*31:0*/ __PVT__normalizer__DOT__scalar_count;
        IData/*31:0*/ __PVT__normalizer__DOT__input_scalar;
        IData/*31:0*/ __PVT__normalizer__DOT__append_scalar;
        IData/*31:0*/ __PVT__normalizer__DOT__insert_position;
        IData/*31:0*/ __PVT__normalizer__DOT__previous_scalar;
        IData/*31:0*/ __PVT__normalizer__DOT__range_count;
        IData/*31:0*/ __PVT__normalizer__DOT__class_count;
        IData/*31:0*/ __PVT__normalizer__DOT__decomposition_count;
        IData/*31:0*/ __PVT__normalizer__DOT__scalar_pool_count;
        IData/*31:0*/ __PVT__normalizer__DOT__composition_count;
        IData/*31:0*/ __PVT__normalizer__DOT__search_low;
        IData/*31:0*/ __PVT__normalizer__DOT__search_high;
        IData/*31:0*/ __PVT__normalizer__DOT__search_middle;
        IData/*31:0*/ __PVT__normalizer__DOT__pool_cursor;
        IData/*31:0*/ __PVT__normalizer__DOT__pool_remaining;
        VlWide<4>/*127:0*/ __PVT__normalizer__DOT__record_value;
        IData/*31:0*/ __PVT__normalizer__DOT__hangul_index;
        IData/*31:0*/ __PVT__normalizer__DOT__hangul_l;
        IData/*31:0*/ __PVT__normalizer__DOT__hangul_v;
        IData/*31:0*/ __PVT__normalizer__DOT__hangul_t;
        IData/*31:0*/ __PVT__normalizer__DOT__hangul_l_index;
        IData/*31:0*/ __PVT__normalizer__DOT__hangul_v_index;
        IData/*31:0*/ __PVT__normalizer__DOT__hangul_product;
        IData/*31:0*/ __PVT__normalizer__DOT__read_index;
        IData/*31:0*/ __PVT__normalizer__DOT__write_index;
        IData/*31:0*/ __PVT__normalizer__DOT__output_index;
        IData/*31:0*/ __PVT__normalizer__DOT__current_scalar;
        IData/*31:0*/ __PVT__normalizer__DOT__starter_scalar;
        IData/*31:0*/ __PVT__normalizer__DOT__starter_position;
        IData/*31:0*/ __PVT__normalizer__DOT__composite_scalar;
        IData/*31:0*/ __PVT__normalizer__DOT__class_properties;
        IData/*31:0*/ __PVT__normalizer__DOT__quotient;
        IData/*31:0*/ __PVT__normalizer__DOT__remainder_value;
        IData/*31:0*/ __PVT__normalizer__DOT__records__DOT__reader__DOT__count;
        IData/*31:0*/ __PVT__normalizer__DOT__records__DOT__reader__DOT__index;
        VlWide<3>/*65:0*/ __PVT__normalizer__DOT__records__DOT__reader__DOT__offset_value;
        VlWide<3>/*65:0*/ __PVT__normalizer__DOT__records__DOT__reader__DOT__data_start;
        VlWide<3>/*65:0*/ __PVT__normalizer__DOT__records__DOT__reader__DOT__table_end;
        VlWide<3>/*65:0*/ __PVT__normalizer__DOT__records__DOT__reader__DOT__request_address;
        VlWide<4>/*127:0*/ __PVT__normalizer__DOT__records__DOT__reader__DOT__result_data;
        IData/*31:0*/ __PVT__normalizer__DOT__records__DOT__reader__DOT__read_data;
        IData/*31:0*/ __PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__count;
        IData/*31:0*/ __PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__index;
        VlWide<3>/*65:0*/ __PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__offset_value;
        VlWide<3>/*65:0*/ __PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__data_start;
    };
    struct {
        VlWide<3>/*65:0*/ __PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__table_end;
        VlWide<3>/*65:0*/ __PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__request_address;
        IData/*31:0*/ __PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__result_data;
        IData/*31:0*/ __PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__read_data;
        IData/*31:0*/ __PVT__normalizer__DOT__classification__DOT__scalar;
        IData/*31:0*/ __PVT__normalizer__DOT__classification__DOT__range_count;
        IData/*31:0*/ __PVT__normalizer__DOT__classification__DOT__class_count;
        IData/*31:0*/ __PVT__normalizer__DOT__classification__DOT__low_index;
        IData/*31:0*/ __PVT__normalizer__DOT__classification__DOT__high_index;
        IData/*31:0*/ __PVT__normalizer__DOT__classification__DOT__middle;
        IData/*31:0*/ __PVT__normalizer__DOT__classification__DOT__first_scalar;
        IData/*31:0*/ __PVT__normalizer__DOT__classification__DOT__last_scalar;
        IData/*31:0*/ __PVT__normalizer__DOT__classification__DOT__class_value;
        IData/*31:0*/ __PVT__normalizer__DOT__classification__DOT__property_value;
        VlWide<4>/*127:0*/ __PVT__normalizer__DOT__classification__DOT__reader_data;
        IData/*31:0*/ __PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__count;
        IData/*31:0*/ __PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__index;
        VlWide<3>/*65:0*/ __PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value;
        VlWide<3>/*65:0*/ __PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__data_start;
        VlWide<3>/*65:0*/ __PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__table_end;
        VlWide<3>/*65:0*/ __PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__request_address;
        VlWide<4>/*127:0*/ __PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data;
        IData/*31:0*/ __PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__read_data;
        IData/*31:0*/ __PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__dividend_shift;
        IData/*31:0*/ __PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__divisor;
        IData/*31:0*/ __PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__quotient_work;
        IData/*31:0*/ __PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__quotient_result;
        IData/*31:0*/ __PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__remainder_result;
        VL_IN64(cfg_ranges_base,63,0);
        VL_IN64(cfg_decomposition_base,63,0);
        VL_IN64(cfg_scalar_pool_base,63,0);
        VL_IN64(cfg_composition_base,63,0);
        VL_OUT64(tbl_req_addr,63,0);
        QData/*63:0*/ __PVT__normalizer__DOT__ranges_base;
        QData/*63:0*/ __PVT__normalizer__DOT__decomposition_base;
        QData/*63:0*/ __PVT__normalizer__DOT__scalar_pool_base;
        QData/*63:0*/ __PVT__normalizer__DOT__composition_base;
        QData/*32:0*/ __PVT__normalizer__DOT__pool_end;
        QData/*63:0*/ __PVT__normalizer__DOT__records__DOT__reader__DOT__base;
        QData/*63:0*/ __PVT__normalizer__DOT__scalar_pool__DOT__reader__DOT__base;
        QData/*63:0*/ __PVT__normalizer__DOT__classification__DOT__base;
        QData/*63:0*/ __PVT__normalizer__DOT__classification__DOT__record_reader__DOT__reader__DOT__base;
        QData/*32:0*/ __PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__remainder_work;
        QData/*32:0*/ __PVT__normalizer__DOT__hangul_divider__DOT__divider__DOT__shifted_remainder;
        VlUnpacked<IData/*31:0*/, 16> __PVT__normalizer__DOT__scalars;
        VlUnpacked<CData/*7:0*/, 16> __PVT__normalizer__DOT__combining_classes;
    };

    // INTERNAL VARIABLES
    Vbench__Syms* const vlSymsp;

    // CONSTRUCTORS
    Vbench_anvil_edge_normalizer__M10(Vbench__Syms* symsp, const char* v__name);
    ~Vbench_anvil_edge_normalizer__M10();
    VL_UNCOPYABLE(Vbench_anvil_edge_normalizer__M10);

    // INTERNAL METHODS
    void __Vconfigure(bool first);
};


#endif  // guard
