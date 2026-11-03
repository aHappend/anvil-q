// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design internal header
// See Vbench.h for the primary calling header

#ifndef VERILATED_VBENCH_ANVIL_Q1_RMSNORM__N1_H8_M4_H_
#define VERILATED_VBENCH_ANVIL_Q1_RMSNORM__N1_H8_M4_H_  // guard

#include "verilated.h"
#include "verilated_timing.h"


class Vbench__Syms;

class alignas(VL_CACHE_LINE_BYTES) Vbench_anvil_q1_rmsnorm__N1_H8_M4 final : public VerilatedModule {
  public:

    // DESIGN SPECIFIC STATE
    // Anonymous structures to workaround compiler member-count bugs
    struct {
        VL_IN8(clk,0,0);
        VL_IN8(rst_n,0,0);
        VL_IN8(cmd_valid,0,0);
        VL_OUT8(cmd_ready,0,0);
        VL_IN8(cmd_mode,1,0);
        VL_OUT8(done,0,0);
        VL_OUT8(error,0,0);
        VL_OUT8(mem_req_valid,0,0);
        VL_IN8(mem_req_ready,0,0);
        VL_OUT8(mem_req_write,0,0);
        VL_OUT8(mem_req_kind,3,0);
        VL_OUT8(mem_req_proj,2,0);
        VL_IN8(mem_rsp_valid,0,0);
        VL_OUT8(mem_rsp_ready,0,0);
        VL_IN8(mem_rsp_error,0,0);
        CData/*4:0*/ __PVT__state;
        CData/*0:0*/ __PVT__failed;
        CData/*3:0*/ __PVT__norm_kind;
        CData/*0:0*/ __PVT__complete;
        CData/*0:0*/ __PVT__fault;
        CData/*0:0*/ __PVT__issue;
        CData/*0:0*/ __PVT__write_request;
        CData/*3:0*/ __PVT__kind;
        CData/*0:0*/ __PVT__multiply_ready;
        CData/*0:0*/ __PVT__multiply_valid;
        CData/*0:0*/ __PVT__divide_ready;
        CData/*0:0*/ __PVT__divide_valid;
        CData/*0:0*/ __PVT__divide_by_zero;
        CData/*0:0*/ __PVT__root_ready;
        CData/*0:0*/ __PVT__root_valid;
        CData/*0:0*/ __Vcellinp__multiplier__out_ready;
        CData/*0:0*/ __Vcellinp__multiplier__in_valid;
        CData/*1:0*/ __PVT__memory_port__DOT__state;
        CData/*0:0*/ __PVT__memory_port__DOT__wr;
        CData/*3:0*/ __PVT__memory_port__DOT__kd;
        CData/*2:0*/ __PVT__memory_port__DOT__pj;
        CData/*0:0*/ __PVT__multiplier__DOT__multiplier__DOT__negative;
        CData/*0:0*/ __PVT__multiplier__DOT__multiplier__DOT__busy;
        CData/*0:0*/ __PVT__multiplier__DOT__multiplier__DOT__valid_result;
        CData/*7:0*/ __PVT__multiplier__DOT__multiplier__DOT__valid_pipe;
        CData/*1:0*/ __PVT__divider__DOT__divider__DOT__state;
        CData/*7:0*/ __PVT__divider__DOT__divider__DOT__iterations;
        CData/*0:0*/ __PVT__divider__DOT__divider__DOT__zero_divisor;
        CData/*0:0*/ __PVT__divider__DOT__divider__DOT__subtract;
        CData/*1:0*/ __PVT__root_unit__DOT__state;
        CData/*5:0*/ __PVT__root_unit__DOT__iteration;
        CData/*0:0*/ __PVT__root_unit__DOT__subtract;
        VL_IN(cmd_layer,31,0);
        VL_IN(cmd_pos,31,0);
        VL_OUT(mem_req_layer,31,0);
        VL_OUT(mem_req_row,31,0);
        VL_OUT(mem_req_col,31,0);
        VL_OUT(mem_req_wdata,31,0);
        VL_IN(mem_rsp_rdata,31,0);
        IData/*31:0*/ __PVT__layer;
        IData/*31:0*/ __PVT__index;
        IData/*31:0*/ __PVT__source_slot;
        IData/*31:0*/ __PVT__target_slot;
        VlWide<3>/*95:0*/ __PVT__sum;
        VlWide<4>/*127:0*/ __PVT__mean;
        IData/*31:0*/ __PVT__x;
        IData/*31:0*/ __PVT__gamma;
        IData/*31:0*/ __PVT__output_value;
        VlWide<4>/*127:0*/ __PVT__scale_product;
    };
    struct {
        IData/*31:0*/ __PVT__read_data;
        IData/*31:0*/ __PVT__memory_layer;
        IData/*31:0*/ __PVT__row;
        IData/*31:0*/ __PVT__write_data;
        VlWide<8>/*255:0*/ __PVT__product;
        VlWide<4>/*127:0*/ __PVT__operand_a;
        VlWide<4>/*127:0*/ __PVT__operand_b;
        VlWide<4>/*127:0*/ __PVT__quotient;
        VlWide<4>/*127:0*/ __Vcellinp__divider__denominator;
        IData/*31:0*/ __PVT__memory_port__DOT__ly;
        IData/*31:0*/ __PVT__memory_port__DOT__rw;
        IData/*31:0*/ __PVT__memory_port__DOT__cl;
        IData/*31:0*/ __PVT__memory_port__DOT__wd;
        VlWide<4>/*127:0*/ __PVT__multiplier__DOT__multiplier__DOT__magnitude_a;
        VlWide<4>/*127:0*/ __PVT__multiplier__DOT__multiplier__DOT__magnitude_b;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__result;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered;
    };
    struct {
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__2__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__3__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__4__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__5__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__6__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__7__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__8__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__9__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__10__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__11__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__12__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__13__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__14__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__15__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__16__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__17__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__18__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__19__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__20__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__21__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__22__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__23__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__24__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__25__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__26__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__27__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__28__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__29__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__30__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__31__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__1__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__2__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__3__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__4__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__5__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__6__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__7__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__8__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__9__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__10__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__11__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__12__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__13__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__14__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__15__KET____DOT__sum;
    };
    struct {
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__0__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__1__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__2__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__3__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__4__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__5__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__6__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__7__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__0__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__1__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__2__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__3__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__5__KET____DOT__adder__BRA__0__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__5__KET____DOT__adder__BRA__1__KET____DOT__sum;
        VlWide<8>/*255:0*/ __PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__6__KET____DOT__adder__BRA__0__KET____DOT__sum;
        VlWide<4>/*127:0*/ __PVT__divider__DOT__divider__DOT__dividend_shift;
        VlWide<4>/*127:0*/ __PVT__divider__DOT__divider__DOT__divisor;
        VlWide<4>/*127:0*/ __PVT__divider__DOT__divider__DOT__quotient_work;
        VlWide<5>/*128:0*/ __PVT__divider__DOT__divider__DOT__remainder_work;
        VlWide<4>/*127:0*/ __PVT__divider__DOT__divider__DOT__quotient_result;
        VlWide<5>/*128:0*/ __PVT__divider__DOT__divider__DOT__shifted_remainder;
        VlWide<4>/*127:0*/ __PVT__root_unit__DOT__radicand_shift;
        VlWide<5>/*129:0*/ __PVT__root_unit__DOT__remainder_work;
        VlWide<5>/*129:0*/ __PVT__root_unit__DOT__shifted_remainder;
        VlWide<5>/*129:0*/ __PVT__root_unit__DOT__trial;
        QData/*63:0*/ __PVT__square_value;
        QData/*63:0*/ __PVT__reciprocal;
        QData/*63:0*/ __PVT__denominator;
        QData/*63:0*/ __PVT__norm_product;
        QData/*63:0*/ __PVT__root_value;
        QData/*63:0*/ __PVT__root_unit__DOT__root_work;
        QData/*63:0*/ __PVT__root_unit__DOT__root_result;
        VlUnpacked<VlUnpacked<VlWide<8>/*255:0*/, 64>, 7> __PVT__multiplier__DOT__multiplier__DOT__tree;
    };

    // INTERNAL VARIABLES
    Vbench__Syms* const vlSymsp;

    // CONSTRUCTORS
    Vbench_anvil_q1_rmsnorm__N1_H8_M4(Vbench__Syms* symsp, const char* v__name);
    ~Vbench_anvil_q1_rmsnorm__N1_H8_M4();
    VL_UNCOPYABLE(Vbench_anvil_q1_rmsnorm__N1_H8_M4);

    // INTERNAL METHODS
    void __Vconfigure(bool first);
};


#endif  // guard
