// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design internal header
// See Vbench.h for the primary calling header

#ifndef VERILATED_VBENCH_ANVIL_EDGE_SPECIAL_SPLITTER__PI7_H_
#define VERILATED_VBENCH_ANVIL_EDGE_SPECIAL_SPLITTER__PI7_H_  // guard

#include "verilated.h"
#include "verilated_timing.h"


class Vbench__Syms;

class alignas(VL_CACHE_LINE_BYTES) Vbench_anvil_edge_special_splitter__pi7 final : public VerilatedModule {
  public:

    // DESIGN SPECIFIC STATE
    // Anonymous structures to workaround compiler member-count bugs
    struct {
        VL_IN8(clk,0,0);
        VL_IN8(rst_n,0,0);
        VL_IN8(start,0,0);
        VL_IN8(config_valid,0,0);
        VL_IN8(normalized_phase,0,0);
        VL_IN8(in_valid,0,0);
        VL_OUT8(in_ready,0,0);
        VL_IN8(in_last,0,0);
        VL_OUT8(out_valid,0,0);
        VL_IN8(out_ready,0,0);
        VL_OUT8(out_special,0,0);
        VL_OUT8(out_boundary,0,0);
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
        CData/*5:0*/ __PVT__splitter__DOT__state;
        CData/*2:0*/ __PVT__splitter__DOT__encoded_remaining;
        CData/*0:0*/ __PVT__splitter__DOT__best_valid;
        CData/*0:0*/ __PVT__splitter__DOT__phase;
        CData/*0:0*/ __PVT__splitter__DOT__output_special;
        CData/*0:0*/ __PVT__splitter__DOT__output_boundary;
        CData/*0:0*/ __PVT__splitter__DOT__output_last;
        CData/*7:0*/ __PVT__splitter__DOT__code;
        CData/*0:0*/ __PVT__splitter__DOT__classify_selected;
        CData/*0:0*/ __PVT__splitter__DOT__edge_selected;
        CData/*0:0*/ __PVT__splitter__DOT__special_selected;
        CData/*0:0*/ __PVT__splitter__DOT__class_ready;
        CData/*0:0*/ __PVT__splitter__DOT__class_valid;
        CData/*0:0*/ __PVT__splitter__DOT__class_req;
        CData/*0:0*/ __PVT__splitter__DOT__class_rsp_ready;
        CData/*0:0*/ __PVT__splitter__DOT__record_ready;
        CData/*0:0*/ __PVT__splitter__DOT__record_valid;
        CData/*0:0*/ __PVT__splitter__DOT__record_error;
        CData/*0:0*/ __PVT__splitter__DOT__record_req;
        CData/*0:0*/ __PVT__splitter__DOT__record_rsp_ready;
        CData/*7:0*/ __PVT__splitter__DOT__record_code;
        CData/*0:0*/ __PVT__splitter__DOT__edge_ready;
        CData/*0:0*/ __PVT__splitter__DOT__edge_valid;
        CData/*0:0*/ __PVT__splitter__DOT__edge_req;
        CData/*0:0*/ __PVT__splitter__DOT__edge_rsp_ready;
        CData/*0:0*/ __PVT__splitter__DOT__encoder_ready;
        CData/*0:0*/ __PVT__splitter__DOT__encoder_valid;
        CData/*0:0*/ __PVT__splitter__DOT__eligible;
        CData/*0:0*/ __Vcellinp__splitter__DOT__encoder__start;
        CData/*0:0*/ __VdfgTmp_hed1c005a__0;
        CData/*3:0*/ __PVT__splitter__DOT__classification__DOT__state;
        CData/*0:0*/ __PVT__splitter__DOT__classification__DOT__admitted;
        CData/*0:0*/ __PVT__splitter__DOT__classification__DOT__failed;
        CData/*7:0*/ __PVT__splitter__DOT__classification__DOT__code;
        CData/*0:0*/ __PVT__splitter__DOT__classification__DOT__reader_ready;
        CData/*0:0*/ __PVT__splitter__DOT__classification__DOT__reader_valid;
        CData/*3:0*/ __PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state;
        CData/*1:0*/ __PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__word_index;
        CData/*0:0*/ __PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__failed;
        CData/*7:0*/ __PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__code;
        CData/*2:0*/ __PVT__splitter__DOT__encoder__DOT__state;
        CData/*2:0*/ __PVT__splitter__DOT__encoder__DOT__remaining;
    };
    struct {
        CData/*0:0*/ __PVT__splitter__DOT__encoder__DOT__final_scalar;
        CData/*7:0*/ __PVT__splitter__DOT__encoder__DOT__code;
        CData/*3:0*/ __PVT__splitter__DOT__records__DOT__reader__DOT__state;
        CData/*1:0*/ __PVT__splitter__DOT__records__DOT__reader__DOT__word_index;
        CData/*0:0*/ __PVT__splitter__DOT__records__DOT__reader__DOT__failed;
        CData/*7:0*/ __PVT__splitter__DOT__records__DOT__reader__DOT__code;
        CData/*3:0*/ __PVT__splitter__DOT__edges__DOT__reader__DOT__state;
        CData/*0:0*/ __PVT__splitter__DOT__edges__DOT__reader__DOT__word_index;
        CData/*0:0*/ __PVT__splitter__DOT__edges__DOT__reader__DOT__failed;
        CData/*7:0*/ __PVT__splitter__DOT__edges__DOT__reader__DOT__code;
        VL_INW(cfg_table_bases,1023,0,32);
        VL_INW(cfg_metadata,1023,0,32);
        VL_INW(cfg_table_counts,511,0,16);
        VL_IN(in_scalar,31,0);
        VL_OUT(out_value,31,0);
        VL_IN(tbl_rsp_data,31,0);
        IData/*31:0*/ __PVT__splitter__DOT__scalar_count;
        IData/*31:0*/ __PVT__splitter__DOT__scalar_index;
        IData/*31:0*/ __PVT__splitter__DOT__byte_count;
        IData/*31:0*/ __PVT__splitter__DOT__scan_index;
        IData/*31:0*/ __PVT__splitter__DOT__cursor;
        IData/*31:0*/ __PVT__splitter__DOT__plan_count;
        IData/*31:0*/ __PVT__splitter__DOT__output_index;
        IData/*31:0*/ __PVT__splitter__DOT__node_index;
        IData/*31:0*/ __PVT__splitter__DOT__edge_first;
        IData/*31:0*/ __PVT__splitter__DOT__edge_count;
        IData/*31:0*/ __PVT__splitter__DOT__edge_cursor;
        IData/*31:0*/ __PVT__splitter__DOT__terminal_index;
        IData/*31:0*/ __PVT__splitter__DOT__best_end;
        IData/*31:0*/ __PVT__splitter__DOT__best_token;
        IData/*31:0*/ __PVT__splitter__DOT__best_flags;
        IData/*31:0*/ __PVT__splitter__DOT__best_record;
        IData/*31:0*/ __PVT__splitter__DOT__output_value;
        VlWide<4>/*127:0*/ __PVT__splitter__DOT__node_record;
        VlWide<4>/*127:0*/ __PVT__splitter__DOT__special_record;
        VlWide<4>/*127:0*/ __PVT__splitter__DOT__record_data;
        IData/*31:0*/ __PVT__splitter__DOT__terminal_end;
        IData/*31:0*/ __PVT__splitter__DOT__special_flags;
        IData/*31:0*/ __Vcellinp__splitter__DOT__classification__in_scalar;
        IData/*31:0*/ __PVT__splitter__DOT__classification__DOT__scalar;
        IData/*31:0*/ __PVT__splitter__DOT__classification__DOT__range_count;
        IData/*31:0*/ __PVT__splitter__DOT__classification__DOT__class_count;
        IData/*31:0*/ __PVT__splitter__DOT__classification__DOT__low_index;
        IData/*31:0*/ __PVT__splitter__DOT__classification__DOT__high_index;
        IData/*31:0*/ __PVT__splitter__DOT__classification__DOT__middle;
        IData/*31:0*/ __PVT__splitter__DOT__classification__DOT__first_scalar;
        IData/*31:0*/ __PVT__splitter__DOT__classification__DOT__last_scalar;
        IData/*31:0*/ __PVT__splitter__DOT__classification__DOT__class_value;
        IData/*31:0*/ __PVT__splitter__DOT__classification__DOT__property_value;
        VlWide<4>/*127:0*/ __PVT__splitter__DOT__classification__DOT__reader_data;
        IData/*31:0*/ __PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__count;
        IData/*31:0*/ __PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__index;
        VlWide<3>/*65:0*/ __PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value;
        VlWide<3>/*65:0*/ __PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__data_start;
        VlWide<3>/*65:0*/ __PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__table_end;
        VlWide<3>/*65:0*/ __PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__request_address;
        VlWide<4>/*127:0*/ __PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data;
        IData/*31:0*/ __PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__read_data;
        IData/*31:0*/ __PVT__splitter__DOT__encoder__DOT__encoded;
        IData/*31:0*/ __PVT__splitter__DOT__records__DOT__reader__DOT__count;
        IData/*31:0*/ __PVT__splitter__DOT__records__DOT__reader__DOT__index;
        VlWide<3>/*65:0*/ __PVT__splitter__DOT__records__DOT__reader__DOT__offset_value;
        VlWide<3>/*65:0*/ __PVT__splitter__DOT__records__DOT__reader__DOT__data_start;
        VlWide<3>/*65:0*/ __PVT__splitter__DOT__records__DOT__reader__DOT__table_end;
    };
    struct {
        VlWide<3>/*65:0*/ __PVT__splitter__DOT__records__DOT__reader__DOT__request_address;
        VlWide<4>/*127:0*/ __PVT__splitter__DOT__records__DOT__reader__DOT__result_data;
        IData/*31:0*/ __PVT__splitter__DOT__records__DOT__reader__DOT__read_data;
        IData/*31:0*/ __PVT__splitter__DOT__edges__DOT__reader__DOT__count;
        IData/*31:0*/ __PVT__splitter__DOT__edges__DOT__reader__DOT__index;
        VlWide<3>/*65:0*/ __PVT__splitter__DOT__edges__DOT__reader__DOT__offset_value;
        VlWide<3>/*65:0*/ __PVT__splitter__DOT__edges__DOT__reader__DOT__data_start;
        VlWide<3>/*65:0*/ __PVT__splitter__DOT__edges__DOT__reader__DOT__table_end;
        VlWide<3>/*65:0*/ __PVT__splitter__DOT__edges__DOT__reader__DOT__request_address;
        IData/*31:0*/ __PVT__splitter__DOT__edges__DOT__reader__DOT__read_data;
        VL_OUT64(tbl_req_addr,63,0);
        QData/*63:0*/ __PVT__splitter__DOT__edge_record;
        QData/*32:0*/ __PVT__splitter__DOT__edge_end;
        QData/*63:0*/ __PVT__splitter__DOT__classification__DOT__base;
        QData/*63:0*/ __PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__base;
        QData/*63:0*/ __PVT__splitter__DOT__records__DOT__reader__DOT__base;
        QData/*63:0*/ __PVT__splitter__DOT__edges__DOT__reader__DOT__base;
        QData/*63:0*/ __PVT__splitter__DOT__edges__DOT__reader__DOT__result_data;
        VlUnpacked<IData/*31:0*/, 16> __PVT__splitter__DOT__scalars;
        VlUnpacked<SData/*9:0*/, 16> __PVT__splitter__DOT__properties;
        VlUnpacked<CData/*7:0*/, 16> __PVT__splitter__DOT__bytes_memory;
        VlUnpacked<IData/*31:0*/, 16> __PVT__splitter__DOT__scalar_starts;
        VlUnpacked<IData/*31:0*/, 16> __PVT__splitter__DOT__byte_ends;
        VlUnpacked<IData/*31:0*/, 16> __PVT__splitter__DOT__plan_value;
        VlUnpacked<CData/*0:0*/, 16> __PVT__splitter__DOT__plan_special;
        VlUnpacked<CData/*0:0*/, 16> __PVT__splitter__DOT__plan_space;
    };

    // INTERNAL VARIABLES
    Vbench__Syms* const vlSymsp;

    // CONSTRUCTORS
    Vbench_anvil_edge_special_splitter__pi7(Vbench__Syms* symsp, const char* v__name);
    ~Vbench_anvil_edge_special_splitter__pi7();
    VL_UNCOPYABLE(Vbench_anvil_edge_special_splitter__pi7);

    // INTERNAL METHODS
    void __Vconfigure(bool first);
};


#endif  // guard
