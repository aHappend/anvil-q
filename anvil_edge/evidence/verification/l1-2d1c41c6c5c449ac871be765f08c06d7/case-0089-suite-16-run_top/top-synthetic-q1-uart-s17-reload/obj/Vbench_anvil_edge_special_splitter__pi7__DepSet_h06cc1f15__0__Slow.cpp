// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vbench.h for the primary calling header

#include "Vbench__pch.h"
#include "Vbench_anvil_edge_special_splitter__pi7.h"

VL_ATTR_COLD void Vbench_anvil_edge_special_splitter__pi7___ctor_var_reset(Vbench_anvil_edge_special_splitter__pi7* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+            Vbench_anvil_edge_special_splitter__pi7___ctor_var_reset\n"); );
    // Body
    vlSelf->clk = VL_RAND_RESET_I(1);
    vlSelf->rst_n = VL_RAND_RESET_I(1);
    vlSelf->start = VL_RAND_RESET_I(1);
    vlSelf->config_valid = VL_RAND_RESET_I(1);
    vlSelf->normalized_phase = VL_RAND_RESET_I(1);
    VL_RAND_RESET_W(1024, vlSelf->cfg_table_bases);
    VL_RAND_RESET_W(1024, vlSelf->cfg_metadata);
    VL_RAND_RESET_W(512, vlSelf->cfg_table_counts);
    vlSelf->in_valid = VL_RAND_RESET_I(1);
    vlSelf->in_ready = VL_RAND_RESET_I(1);
    vlSelf->in_scalar = VL_RAND_RESET_I(32);
    vlSelf->in_last = VL_RAND_RESET_I(1);
    vlSelf->out_valid = VL_RAND_RESET_I(1);
    vlSelf->out_ready = VL_RAND_RESET_I(1);
    vlSelf->out_value = VL_RAND_RESET_I(32);
    vlSelf->out_special = VL_RAND_RESET_I(1);
    vlSelf->out_boundary = VL_RAND_RESET_I(1);
    vlSelf->out_last = VL_RAND_RESET_I(1);
    vlSelf->__PVT__busy = VL_RAND_RESET_I(1);
    vlSelf->__PVT__done = VL_RAND_RESET_I(1);
    vlSelf->error = VL_RAND_RESET_I(1);
    vlSelf->error_code = VL_RAND_RESET_I(8);
    vlSelf->tbl_req_valid = VL_RAND_RESET_I(1);
    vlSelf->tbl_req_ready = VL_RAND_RESET_I(1);
    vlSelf->tbl_req_addr = VL_RAND_RESET_Q(64);
    vlSelf->tbl_rsp_valid = VL_RAND_RESET_I(1);
    vlSelf->tbl_rsp_ready = VL_RAND_RESET_I(1);
    vlSelf->tbl_rsp_data = VL_RAND_RESET_I(32);
    vlSelf->tbl_rsp_error = VL_RAND_RESET_I(1);
    vlSelf->__PVT__splitter__DOT__state = VL_RAND_RESET_I(6);
    for (int __Vi0 = 0; __Vi0 < 16; ++__Vi0) {
        vlSelf->__PVT__splitter__DOT__scalars[__Vi0] = VL_RAND_RESET_I(32);
    }
    for (int __Vi0 = 0; __Vi0 < 16; ++__Vi0) {
        vlSelf->__PVT__splitter__DOT__properties[__Vi0] = VL_RAND_RESET_I(10);
    }
    for (int __Vi0 = 0; __Vi0 < 16; ++__Vi0) {
        vlSelf->__PVT__splitter__DOT__bytes_memory[__Vi0] = VL_RAND_RESET_I(8);
    }
    for (int __Vi0 = 0; __Vi0 < 16; ++__Vi0) {
        vlSelf->__PVT__splitter__DOT__scalar_starts[__Vi0] = VL_RAND_RESET_I(32);
    }
    for (int __Vi0 = 0; __Vi0 < 16; ++__Vi0) {
        vlSelf->__PVT__splitter__DOT__byte_ends[__Vi0] = VL_RAND_RESET_I(32);
    }
    for (int __Vi0 = 0; __Vi0 < 16; ++__Vi0) {
        vlSelf->__PVT__splitter__DOT__plan_value[__Vi0] = VL_RAND_RESET_I(32);
    }
    for (int __Vi0 = 0; __Vi0 < 16; ++__Vi0) {
        vlSelf->__PVT__splitter__DOT__plan_special[__Vi0] = VL_RAND_RESET_I(1);
    }
    for (int __Vi0 = 0; __Vi0 < 16; ++__Vi0) {
        vlSelf->__PVT__splitter__DOT__plan_space[__Vi0] = VL_RAND_RESET_I(1);
    }
    vlSelf->__PVT__splitter__DOT__scalar_count = VL_RAND_RESET_I(32);
    vlSelf->__PVT__splitter__DOT__scalar_index = VL_RAND_RESET_I(32);
    vlSelf->__PVT__splitter__DOT__byte_count = VL_RAND_RESET_I(32);
    vlSelf->__PVT__splitter__DOT__scan_index = VL_RAND_RESET_I(32);
    vlSelf->__PVT__splitter__DOT__cursor = VL_RAND_RESET_I(32);
    vlSelf->__PVT__splitter__DOT__plan_count = VL_RAND_RESET_I(32);
    vlSelf->__PVT__splitter__DOT__output_index = VL_RAND_RESET_I(32);
    vlSelf->__PVT__splitter__DOT__encoded_remaining = VL_RAND_RESET_I(3);
    vlSelf->__PVT__splitter__DOT__node_index = VL_RAND_RESET_I(32);
    vlSelf->__PVT__splitter__DOT__edge_first = VL_RAND_RESET_I(32);
    vlSelf->__PVT__splitter__DOT__edge_count = VL_RAND_RESET_I(32);
    vlSelf->__PVT__splitter__DOT__edge_cursor = VL_RAND_RESET_I(32);
    vlSelf->__PVT__splitter__DOT__terminal_index = VL_RAND_RESET_I(32);
    vlSelf->__PVT__splitter__DOT__best_end = VL_RAND_RESET_I(32);
    vlSelf->__PVT__splitter__DOT__best_token = VL_RAND_RESET_I(32);
    vlSelf->__PVT__splitter__DOT__best_flags = VL_RAND_RESET_I(32);
    vlSelf->__PVT__splitter__DOT__best_record = VL_RAND_RESET_I(32);
    vlSelf->__PVT__splitter__DOT__best_valid = VL_RAND_RESET_I(1);
    vlSelf->__PVT__splitter__DOT__phase = VL_RAND_RESET_I(1);
    vlSelf->__PVT__splitter__DOT__output_value = VL_RAND_RESET_I(32);
    vlSelf->__PVT__splitter__DOT__output_special = VL_RAND_RESET_I(1);
    vlSelf->__PVT__splitter__DOT__output_boundary = VL_RAND_RESET_I(1);
    vlSelf->__PVT__splitter__DOT__output_last = VL_RAND_RESET_I(1);
    VL_RAND_RESET_W(128, vlSelf->__PVT__splitter__DOT__node_record);
    VL_RAND_RESET_W(128, vlSelf->__PVT__splitter__DOT__special_record);
    vlSelf->__PVT__splitter__DOT__edge_record = VL_RAND_RESET_Q(64);
    vlSelf->__PVT__splitter__DOT__code = VL_RAND_RESET_I(8);
    vlSelf->__PVT__splitter__DOT__classify_selected = VL_RAND_RESET_I(1);
    vlSelf->__PVT__splitter__DOT__edge_selected = VL_RAND_RESET_I(1);
    vlSelf->__PVT__splitter__DOT__special_selected = VL_RAND_RESET_I(1);
    vlSelf->__PVT__splitter__DOT__class_ready = VL_RAND_RESET_I(1);
    vlSelf->__PVT__splitter__DOT__class_valid = VL_RAND_RESET_I(1);
    vlSelf->__PVT__splitter__DOT__class_req = VL_RAND_RESET_I(1);
    vlSelf->__PVT__splitter__DOT__class_rsp_ready = VL_RAND_RESET_I(1);
    vlSelf->__PVT__splitter__DOT__record_ready = VL_RAND_RESET_I(1);
    vlSelf->__PVT__splitter__DOT__record_valid = VL_RAND_RESET_I(1);
    vlSelf->__PVT__splitter__DOT__record_error = VL_RAND_RESET_I(1);
    vlSelf->__PVT__splitter__DOT__record_req = VL_RAND_RESET_I(1);
    vlSelf->__PVT__splitter__DOT__record_rsp_ready = VL_RAND_RESET_I(1);
    VL_RAND_RESET_W(128, vlSelf->__PVT__splitter__DOT__record_data);
    vlSelf->__PVT__splitter__DOT__record_code = VL_RAND_RESET_I(8);
    vlSelf->__PVT__splitter__DOT__edge_ready = VL_RAND_RESET_I(1);
    vlSelf->__PVT__splitter__DOT__edge_valid = VL_RAND_RESET_I(1);
    vlSelf->__PVT__splitter__DOT__edge_req = VL_RAND_RESET_I(1);
    vlSelf->__PVT__splitter__DOT__edge_rsp_ready = VL_RAND_RESET_I(1);
    vlSelf->__PVT__splitter__DOT__encoder_ready = VL_RAND_RESET_I(1);
    vlSelf->__PVT__splitter__DOT__encoder_valid = VL_RAND_RESET_I(1);
    vlSelf->__PVT__splitter__DOT__edge_end = VL_RAND_RESET_Q(33);
    vlSelf->__PVT__splitter__DOT__terminal_end = VL_RAND_RESET_I(32);
    vlSelf->__PVT__splitter__DOT__special_flags = VL_RAND_RESET_I(32);
    vlSelf->__PVT__splitter__DOT__eligible = VL_RAND_RESET_I(1);
    vlSelf->__Vcellinp__splitter__DOT__classification__in_scalar = VL_RAND_RESET_I(32);
    vlSelf->__Vcellinp__splitter__DOT__encoder__start = VL_RAND_RESET_I(1);
    vlSelf->__VdfgTmp_hed1c005a__0 = 0;
    vlSelf->__PVT__splitter__DOT__classification__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->__PVT__splitter__DOT__classification__DOT__admitted = VL_RAND_RESET_I(1);
    vlSelf->__PVT__splitter__DOT__classification__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->__PVT__splitter__DOT__classification__DOT__code = VL_RAND_RESET_I(8);
    vlSelf->__PVT__splitter__DOT__classification__DOT__base = VL_RAND_RESET_Q(64);
    vlSelf->__PVT__splitter__DOT__classification__DOT__scalar = VL_RAND_RESET_I(32);
    vlSelf->__PVT__splitter__DOT__classification__DOT__range_count = VL_RAND_RESET_I(32);
    vlSelf->__PVT__splitter__DOT__classification__DOT__class_count = VL_RAND_RESET_I(32);
    vlSelf->__PVT__splitter__DOT__classification__DOT__low_index = VL_RAND_RESET_I(32);
    vlSelf->__PVT__splitter__DOT__classification__DOT__high_index = VL_RAND_RESET_I(32);
    vlSelf->__PVT__splitter__DOT__classification__DOT__middle = VL_RAND_RESET_I(32);
    vlSelf->__PVT__splitter__DOT__classification__DOT__first_scalar = VL_RAND_RESET_I(32);
    vlSelf->__PVT__splitter__DOT__classification__DOT__last_scalar = VL_RAND_RESET_I(32);
    vlSelf->__PVT__splitter__DOT__classification__DOT__class_value = VL_RAND_RESET_I(32);
    vlSelf->__PVT__splitter__DOT__classification__DOT__property_value = VL_RAND_RESET_I(32);
    vlSelf->__PVT__splitter__DOT__classification__DOT__reader_ready = VL_RAND_RESET_I(1);
    vlSelf->__PVT__splitter__DOT__classification__DOT__reader_valid = VL_RAND_RESET_I(1);
    VL_RAND_RESET_W(128, vlSelf->__PVT__splitter__DOT__classification__DOT__reader_data);
    vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__base = VL_RAND_RESET_Q(64);
    vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__count = VL_RAND_RESET_I(32);
    vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__index = VL_RAND_RESET_I(32);
    vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__word_index = VL_RAND_RESET_I(2);
    VL_RAND_RESET_W(66, vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value);
    VL_RAND_RESET_W(66, vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__data_start);
    VL_RAND_RESET_W(66, vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__table_end);
    VL_RAND_RESET_W(66, vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__request_address);
    VL_RAND_RESET_W(128, vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data);
    vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__read_data = VL_RAND_RESET_I(32);
    vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->__PVT__splitter__DOT__classification__DOT__record_reader__DOT__reader__DOT__code = VL_RAND_RESET_I(8);
    vlSelf->__PVT__splitter__DOT__encoder__DOT__state = VL_RAND_RESET_I(3);
    vlSelf->__PVT__splitter__DOT__encoder__DOT__remaining = VL_RAND_RESET_I(3);
    vlSelf->__PVT__splitter__DOT__encoder__DOT__encoded = VL_RAND_RESET_I(32);
    vlSelf->__PVT__splitter__DOT__encoder__DOT__final_scalar = VL_RAND_RESET_I(1);
    vlSelf->__PVT__splitter__DOT__encoder__DOT__code = VL_RAND_RESET_I(8);
    vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__base = VL_RAND_RESET_Q(64);
    vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__count = VL_RAND_RESET_I(32);
    vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__index = VL_RAND_RESET_I(32);
    vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__word_index = VL_RAND_RESET_I(2);
    VL_RAND_RESET_W(66, vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__offset_value);
    VL_RAND_RESET_W(66, vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__data_start);
    VL_RAND_RESET_W(66, vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__table_end);
    VL_RAND_RESET_W(66, vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__request_address);
    VL_RAND_RESET_W(128, vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__result_data);
    vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__read_data = VL_RAND_RESET_I(32);
    vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->__PVT__splitter__DOT__records__DOT__reader__DOT__code = VL_RAND_RESET_I(8);
    vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__base = VL_RAND_RESET_Q(64);
    vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__count = VL_RAND_RESET_I(32);
    vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__index = VL_RAND_RESET_I(32);
    vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__word_index = VL_RAND_RESET_I(1);
    VL_RAND_RESET_W(66, vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__offset_value);
    VL_RAND_RESET_W(66, vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__data_start);
    VL_RAND_RESET_W(66, vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__table_end);
    VL_RAND_RESET_W(66, vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__request_address);
    vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__result_data = VL_RAND_RESET_Q(64);
    vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__read_data = VL_RAND_RESET_I(32);
    vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->__PVT__splitter__DOT__edges__DOT__reader__DOT__code = VL_RAND_RESET_I(8);
}
