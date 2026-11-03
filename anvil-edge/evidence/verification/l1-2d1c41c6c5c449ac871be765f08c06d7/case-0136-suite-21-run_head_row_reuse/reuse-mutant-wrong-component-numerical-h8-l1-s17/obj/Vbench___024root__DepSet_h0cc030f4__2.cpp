// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vbench.h for the primary calling header

#include "Vbench__pch.h"
#include "Vbench__Syms.h"
#include "Vbench___024root.h"

VL_INLINE_OPT void Vbench___024root___nba_comb__TOP__3(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___nba_comb__TOP__3\n"); );
    // Init
    IData/*31:0*/ bench__DOT__dut__DOT____Vcellout__decoder____pinNumber17;
    bench__DOT__dut__DOT____Vcellout__decoder____pinNumber17 = 0;
    IData/*31:0*/ bench__DOT__dut__DOT____Vcellout__decoder____pinNumber16;
    bench__DOT__dut__DOT____Vcellout__decoder____pinNumber16 = 0;
    IData/*31:0*/ bench__DOT__dut__DOT____Vcellout__decoder____pinNumber15;
    bench__DOT__dut__DOT____Vcellout__decoder____pinNumber15 = 0;
    CData/*2:0*/ bench__DOT__dut__DOT____Vcellout__decoder____pinNumber14;
    bench__DOT__dut__DOT____Vcellout__decoder____pinNumber14 = 0;
    IData/*31:0*/ bench__DOT__dut__DOT____Vcellout__decoder____pinNumber13;
    bench__DOT__dut__DOT____Vcellout__decoder____pinNumber13 = 0;
    CData/*3:0*/ bench__DOT__dut__DOT____Vcellout__decoder____pinNumber12;
    bench__DOT__dut__DOT____Vcellout__decoder____pinNumber12 = 0;
    CData/*0:0*/ bench__DOT__dut__DOT____Vcellout__decoder____pinNumber11;
    bench__DOT__dut__DOT____Vcellout__decoder____pinNumber11 = 0;
    CData/*0:0*/ bench__DOT__dut__DOT____Vcellout__decoder____pinNumber9;
    bench__DOT__dut__DOT____Vcellout__decoder____pinNumber9 = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__decoder__DOT____Vcellinp__mlp____pinNumber21;
    bench__DOT__dut__DOT__decoder__DOT____Vcellinp__mlp____pinNumber21 = 0;
    IData/*31:0*/ bench__DOT__dut__DOT__decoder__DOT____Vcellinp__mlp____pinNumber20;
    bench__DOT__dut__DOT__decoder__DOT____Vcellinp__mlp____pinNumber20 = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__decoder__DOT____Vcellinp__mlp____pinNumber10;
    bench__DOT__dut__DOT__decoder__DOT____Vcellinp__mlp____pinNumber10 = 0;
    VlWide<5>/*136:0*/ bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0;
    VL_ZERO_W(137, bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0);
    VlWide<5>/*136:0*/ bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0;
    VL_ZERO_W(137, bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0);
    VlWide<5>/*136:0*/ bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0;
    VL_ZERO_W(137, bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0);
    VlWide<9>/*287:0*/ __Vtemp_14;
    VlWide<26>/*831:0*/ __Vtemp_59;
    VlWide<13>/*415:0*/ __Vtemp_83;
    // Body
    __Vtemp_14[0U] = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber18;
    __Vtemp_14[1U] = (IData)((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber16)) 
                               << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber17))));
    __Vtemp_14[2U] = (IData)(((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber16)) 
                                << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber17))) 
                              >> 0x20U));
    __Vtemp_14[3U] = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber14 
                       << 3U) | (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber15));
    __Vtemp_14[4U] = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber18 
                       << 9U) | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber10) 
                                  << 8U) | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber12) 
                                             << 7U) 
                                            | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber13) 
                                                << 3U) 
                                               | (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber14 
                                                  >> 0x1dU)))));
    __Vtemp_14[5U] = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber18 
                       >> 0x17U) | ((IData)((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber16)) 
                                              << 0x20U) 
                                             | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber17)))) 
                                    << 9U));
    __Vtemp_14[6U] = (((IData)((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber16)) 
                                 << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber17)))) 
                       >> 0x17U) | ((IData)(((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber16)) 
                                               << 0x20U) 
                                              | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber17))) 
                                             >> 0x20U)) 
                                    << 9U));
    __Vtemp_14[7U] = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber14 
                       << 0xcU) | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber15) 
                                    << 9U) | ((IData)(
                                                      ((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber16)) 
                                                         << 0x20U) 
                                                        | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber17))) 
                                                       >> 0x20U)) 
                                              >> 0x17U)));
    __Vtemp_14[8U] = (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber10) 
                       << 0x11U) | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber12) 
                                     << 0x10U) | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber13) 
                                                   << 0xcU) 
                                                  | (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber14 
                                                     >> 0x14U))));
    if ((0x111U >= (0x1ffU & ((IData)(0x89U) * ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                 ? 1U
                                                 : 0U))))) {
        bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[0U] 
            = (((0U == (0x1fU & ((IData)(0x89U) * ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                    ? 1U
                                                    : 0U))))
                 ? 0U : (__Vtemp_14[((IData)(1U) + 
                                     (0xfU & (((IData)(0x89U) 
                                               * ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                   ? 1U
                                                   : 0U)) 
                                              >> 5U)))] 
                         << ((IData)(0x20U) - (0x1fU 
                                               & ((IData)(0x89U) 
                                                  * 
                                                  ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                    ? 1U
                                                    : 0U)))))) 
               | (__Vtemp_14[(0xfU & (((IData)(0x89U) 
                                       * ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                           ? 1U : 0U)) 
                                      >> 5U))] >> (0x1fU 
                                                   & ((IData)(0x89U) 
                                                      * 
                                                      ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                        ? 1U
                                                        : 0U)))));
        bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[1U] 
            = (((0U == (0x1fU & ((IData)(0x89U) * ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                    ? 1U
                                                    : 0U))))
                 ? 0U : (__Vtemp_14[((IData)(2U) + 
                                     (0xfU & (((IData)(0x89U) 
                                               * ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                   ? 1U
                                                   : 0U)) 
                                              >> 5U)))] 
                         << ((IData)(0x20U) - (0x1fU 
                                               & ((IData)(0x89U) 
                                                  * 
                                                  ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                    ? 1U
                                                    : 0U)))))) 
               | (__Vtemp_14[((IData)(1U) + (0xfU & 
                                             (((IData)(0x89U) 
                                               * ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                   ? 1U
                                                   : 0U)) 
                                              >> 5U)))] 
                  >> (0x1fU & ((IData)(0x89U) * ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                  ? 1U
                                                  : 0U)))));
        bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[2U] 
            = (((0U == (0x1fU & ((IData)(0x89U) * ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                    ? 1U
                                                    : 0U))))
                 ? 0U : (__Vtemp_14[((IData)(3U) + 
                                     (0xfU & (((IData)(0x89U) 
                                               * ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                   ? 1U
                                                   : 0U)) 
                                              >> 5U)))] 
                         << ((IData)(0x20U) - (0x1fU 
                                               & ((IData)(0x89U) 
                                                  * 
                                                  ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                    ? 1U
                                                    : 0U)))))) 
               | (__Vtemp_14[((IData)(2U) + (0xfU & 
                                             (((IData)(0x89U) 
                                               * ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                   ? 1U
                                                   : 0U)) 
                                              >> 5U)))] 
                  >> (0x1fU & ((IData)(0x89U) * ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                  ? 1U
                                                  : 0U)))));
        bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[3U] 
            = (((0U == (0x1fU & ((IData)(0x89U) * ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                    ? 1U
                                                    : 0U))))
                 ? 0U : (__Vtemp_14[((IData)(4U) + 
                                     (0xfU & (((IData)(0x89U) 
                                               * ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                   ? 1U
                                                   : 0U)) 
                                              >> 5U)))] 
                         << ((IData)(0x20U) - (0x1fU 
                                               & ((IData)(0x89U) 
                                                  * 
                                                  ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                    ? 1U
                                                    : 0U)))))) 
               | (__Vtemp_14[((IData)(3U) + (0xfU & 
                                             (((IData)(0x89U) 
                                               * ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                   ? 1U
                                                   : 0U)) 
                                              >> 5U)))] 
                  >> (0x1fU & ((IData)(0x89U) * ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                  ? 1U
                                                  : 0U)))));
        bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[4U] 
            = (0x1ffU & (((0U == (0x1fU & ((IData)(0x89U) 
                                           * ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                               ? 1U
                                               : 0U))))
                           ? 0U : (__Vtemp_14[((IData)(5U) 
                                               + (0xfU 
                                                  & (((IData)(0x89U) 
                                                      * 
                                                      ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                        ? 1U
                                                        : 0U)) 
                                                     >> 5U)))] 
                                   << ((IData)(0x20U) 
                                       - (0x1fU & ((IData)(0x89U) 
                                                   * 
                                                   ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                     ? 1U
                                                     : 0U)))))) 
                         | (__Vtemp_14[((IData)(4U) 
                                        + (0xfU & (
                                                   ((IData)(0x89U) 
                                                    * 
                                                    ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                      ? 1U
                                                      : 0U)) 
                                                   >> 5U)))] 
                            >> (0x1fU & ((IData)(0x89U) 
                                         * ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                             ? 1U : 0U))))));
    } else {
        bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[0U] 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____Vxrand_had98437b__0[0U];
        bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[1U] 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____Vxrand_had98437b__0[1U];
        bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[2U] 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____Vxrand_had98437b__0[2U];
        bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[3U] 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____Vxrand_had98437b__0[3U];
        bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[4U] 
            = (0x1ffU & vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____Vxrand_had98437b__0[4U]);
    }
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT__mux__DOT__active 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (2U 
                                                 > 
                                                 ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                   ? 1U
                                                   : 0U)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT__mux__DOT__active 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (6U 
                                                 > vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected));
    if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT__mux__DOT__active) {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h7a913e59__0 
            = (1U == ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                       ? 1U : 0U));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h7b2ffeda__0 
            = (0U == ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                       ? 1U : 0U));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber9 
            = (1U & (bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[4U] 
                     >> 8U));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber11 
            = (1U & (bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[4U] 
                     >> 7U));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber12 
            = (0xfU & (bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[4U] 
                       >> 3U));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber13 
            = ((bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[4U] 
                << 0x1dU) | (bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[3U] 
                             >> 3U));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber14 
            = (7U & bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[3U]);
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber15 
            = bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[2U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber16 
            = bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[1U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber17 
            = bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[0U];
    } else {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h7a913e59__0 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h7b2ffeda__0 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber9 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber11 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber12 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber13 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber14 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber15 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber16 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber17 = 0U;
    }
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75229de2__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT__mux__DOT__active) 
           & (5U == vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6bb569cc__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT__mux__DOT__active) 
           & (3U == vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6b8ead47__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT__mux__DOT__active) 
           & (2U == vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75d30c27__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT__mux__DOT__active) 
           & (1U == vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6bb6cca2__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT__mux__DOT__active) 
           & (0U == vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75247847__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT__mux__DOT__active) 
           & (4U == vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected));
    __Vtemp_59[0U] = vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__norm.mem_req_wdata;
    __Vtemp_59[1U] = (IData)((((QData)((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__norm.mem_req_row)) 
                               << 0x20U) | (QData)((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__norm.mem_req_col))));
    __Vtemp_59[2U] = (IData)(((((QData)((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__norm.mem_req_row)) 
                                << 0x20U) | (QData)((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__norm.mem_req_col))) 
                              >> 0x20U));
    __Vtemp_59[3U] = ((vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__norm.mem_req_layer 
                       << 3U) | (IData)(vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__norm.mem_req_proj));
    __Vtemp_59[4U] = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber18 
                       << 9U) | (((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__norm.mem_req_valid) 
                                  << 8U) | (((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__norm.mem_req_write) 
                                             << 7U) 
                                            | (((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__norm.mem_req_kind) 
                                                << 3U) 
                                               | (vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__norm.mem_req_layer 
                                                  >> 0x1dU)))));
    __Vtemp_59[5U] = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber18 
                       >> 0x17U) | ((IData)((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber16)) 
                                              << 0x20U) 
                                             | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber17)))) 
                                    << 9U));
    __Vtemp_59[6U] = (((IData)((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber16)) 
                                 << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber17)))) 
                       >> 0x17U) | ((IData)(((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber16)) 
                                               << 0x20U) 
                                              | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber17))) 
                                             >> 0x20U)) 
                                    << 9U));
    __Vtemp_59[7U] = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber14 
                       << 0xcU) | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber15) 
                                    << 9U) | ((IData)(
                                                      ((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber16)) 
                                                         << 0x20U) 
                                                        | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber17))) 
                                                       >> 0x20U)) 
                                              >> 0x17U)));
    __Vtemp_59[8U] = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber17 
                       << 0x12U) | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber10) 
                                     << 0x11U) | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber12) 
                                                   << 0x10U) 
                                                  | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber13) 
                                                      << 0xcU) 
                                                     | (vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber14 
                                                        >> 0x14U)))));
    __Vtemp_59[9U] = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber17 
                       >> 0xeU) | ((IData)((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber15)) 
                                             << 0x20U) 
                                            | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber16)))) 
                                   << 0x12U));
    __Vtemp_59[0xaU] = (((IData)((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber15)) 
                                   << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber16)))) 
                         >> 0xeU) | ((IData)(((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber15)) 
                                                << 0x20U) 
                                               | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber16))) 
                                              >> 0x20U)) 
                                     << 0x12U));
    __Vtemp_59[0xbU] = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber13 
                         << 0x15U) | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber14) 
                                       << 0x12U) | 
                                      ((IData)(((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber15)) 
                                                  << 0x20U) 
                                                 | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber16))) 
                                                >> 0x20U)) 
                                       >> 0xeU)));
    __Vtemp_59[0xcU] = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber17 
                         << 0x1bU) | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber9) 
                                       << 0x1aU) | 
                                      (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber11) 
                                        << 0x19U) | 
                                       (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber12) 
                                         << 0x15U) 
                                        | (vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber13 
                                           >> 0xbU)))));
    __Vtemp_59[0xdU] = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber17 
                         >> 5U) | ((IData)((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber15)) 
                                             << 0x20U) 
                                            | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber16)))) 
                                   << 0x1bU));
    __Vtemp_59[0xeU] = (((IData)((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber15)) 
                                   << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber16)))) 
                         >> 5U) | ((IData)(((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber15)) 
                                              << 0x20U) 
                                             | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber16))) 
                                            >> 0x20U)) 
                                   << 0x1bU));
    __Vtemp_59[0xfU] = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber13 
                         << 0x1eU) | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber14) 
                                       << 0x1bU) | 
                                      ((IData)(((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber15)) 
                                                  << 0x20U) 
                                                 | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber16))) 
                                                >> 0x20U)) 
                                       >> 5U)));
    __Vtemp_59[0x10U] = (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber12) 
                          << 0x1eU) | (vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber13 
                                       >> 2U));
    __Vtemp_59[0x11U] = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber17 
                          << 4U) | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber9) 
                                     << 3U) | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber11) 
                                                << 2U) 
                                               | ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber12) 
                                                  >> 2U))));
    __Vtemp_59[0x12U] = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber17 
                          >> 0x1cU) | ((IData)((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber15)) 
                                                 << 0x20U) 
                                                | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber16)))) 
                                       << 4U));
    __Vtemp_59[0x13U] = (((IData)((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber15)) 
                                    << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber16)))) 
                          >> 0x1cU) | ((IData)(((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber15)) 
                                                  << 0x20U) 
                                                 | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber16))) 
                                                >> 0x20U)) 
                                       << 4U));
    __Vtemp_59[0x14U] = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber13 
                          << 7U) | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber14) 
                                     << 4U) | ((IData)(
                                                       ((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber15)) 
                                                          << 0x20U) 
                                                         | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber16))) 
                                                        >> 0x20U)) 
                                               >> 0x1cU)));
    __Vtemp_59[0x15U] = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber18 
                          << 0xdU) | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber9) 
                                       << 0xcU) | (
                                                   ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber11) 
                                                    << 0xbU) 
                                                   | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber12) 
                                                       << 7U) 
                                                      | (vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber13 
                                                         >> 0x19U)))));
    __Vtemp_59[0x16U] = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber18 
                          >> 0x13U) | ((IData)((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber16)) 
                                                 << 0x20U) 
                                                | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber17)))) 
                                       << 0xdU));
    __Vtemp_59[0x17U] = (((IData)((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber16)) 
                                    << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber17)))) 
                          >> 0x13U) | ((IData)(((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber16)) 
                                                  << 0x20U) 
                                                 | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber17))) 
                                                >> 0x20U)) 
                                       << 0xdU));
    __Vtemp_59[0x18U] = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber14 
                          << 0x10U) | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber15) 
                                        << 0xdU) | 
                                       ((IData)(((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber16)) 
                                                   << 0x20U) 
                                                  | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber17))) 
                                                 >> 0x20U)) 
                                        >> 0x13U)));
    __Vtemp_59[0x19U] = (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber10) 
                          << 0x15U) | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber12) 
                                        << 0x14U) | 
                                       (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber13) 
                                         << 0x10U) 
                                        | (vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber14 
                                           >> 0x10U))));
    if ((0x335U >= (0x3ffU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected)))) {
        bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[0U] 
            = (((0U == (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected)))
                 ? 0U : (__Vtemp_59[((IData)(1U) + 
                                     (0x1fU & (((IData)(0x89U) 
                                                * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected) 
                                               >> 5U)))] 
                         << ((IData)(0x20U) - (0x1fU 
                                               & ((IData)(0x89U) 
                                                  * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected))))) 
               | (__Vtemp_59[(0x1fU & (((IData)(0x89U) 
                                        * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected) 
                                       >> 5U))] >> 
                  (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected))));
        bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[1U] 
            = (((0U == (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected)))
                 ? 0U : (__Vtemp_59[((IData)(2U) + 
                                     (0x1fU & (((IData)(0x89U) 
                                                * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected) 
                                               >> 5U)))] 
                         << ((IData)(0x20U) - (0x1fU 
                                               & ((IData)(0x89U) 
                                                  * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected))))) 
               | (__Vtemp_59[((IData)(1U) + (0x1fU 
                                             & (((IData)(0x89U) 
                                                 * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected) 
                                                >> 5U)))] 
                  >> (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected))));
        bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[2U] 
            = (((0U == (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected)))
                 ? 0U : (__Vtemp_59[((IData)(3U) + 
                                     (0x1fU & (((IData)(0x89U) 
                                                * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected) 
                                               >> 5U)))] 
                         << ((IData)(0x20U) - (0x1fU 
                                               & ((IData)(0x89U) 
                                                  * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected))))) 
               | (__Vtemp_59[((IData)(2U) + (0x1fU 
                                             & (((IData)(0x89U) 
                                                 * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected) 
                                                >> 5U)))] 
                  >> (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected))));
        bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[3U] 
            = (((0U == (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected)))
                 ? 0U : (__Vtemp_59[((IData)(4U) + 
                                     (0x1fU & (((IData)(0x89U) 
                                                * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected) 
                                               >> 5U)))] 
                         << ((IData)(0x20U) - (0x1fU 
                                               & ((IData)(0x89U) 
                                                  * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected))))) 
               | (__Vtemp_59[((IData)(3U) + (0x1fU 
                                             & (((IData)(0x89U) 
                                                 * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected) 
                                                >> 5U)))] 
                  >> (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected))));
        bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[4U] 
            = (0x1ffU & (((0U == (0x1fU & ((IData)(0x89U) 
                                           * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected)))
                           ? 0U : (__Vtemp_59[((IData)(5U) 
                                               + (0x1fU 
                                                  & (((IData)(0x89U) 
                                                      * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected) 
                                                     >> 5U)))] 
                                   << ((IData)(0x20U) 
                                       - (0x1fU & ((IData)(0x89U) 
                                                   * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected))))) 
                         | (__Vtemp_59[((IData)(4U) 
                                        + (0x1fU & 
                                           (((IData)(0x89U) 
                                             * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected) 
                                            >> 5U)))] 
                            >> (0x1fU & ((IData)(0x89U) 
                                         * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected)))));
    } else {
        bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[0U] 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____Vxrand_had98437b__0[0U];
        bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[1U] 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____Vxrand_had98437b__0[1U];
        bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[2U] 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____Vxrand_had98437b__0[2U];
        bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[3U] 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____Vxrand_had98437b__0[3U];
        bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[4U] 
            = (0x1ffU & vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____Vxrand_had98437b__0[4U]);
    }
    if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75229de2__0) {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__residual____pinNumber11 
            = vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber10;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__residual____pinNumber22 
            = vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber21;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__residual____pinNumber21 
            = vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber20;
    } else {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__residual____pinNumber11 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__residual____pinNumber22 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__residual____pinNumber21 = 0U;
    }
    if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6bb569cc__0) {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__attention____pinNumber10 
            = vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber10;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__attention____pinNumber21 
            = vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber21;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__attention____pinNumber20 
            = vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber20;
    } else {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__attention____pinNumber10 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__attention____pinNumber21 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__attention____pinNumber20 = 0U;
    }
    if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6b8ead47__0) {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__rope____pinNumber10 
            = vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber10;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__rope____pinNumber21 
            = vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber21;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__rope____pinNumber20 
            = vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber20;
    } else {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__rope____pinNumber10 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__rope____pinNumber21 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__rope____pinNumber20 = 0U;
    }
    if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75d30c27__0) {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__gemv____pinNumber11 
            = vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber10;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__gemv____pinNumber21 
            = vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber20;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__gemv____pinNumber22 
            = vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber21;
    } else {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__gemv____pinNumber11 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__gemv____pinNumber21 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__gemv____pinNumber22 = 0U;
    }
    if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6bb6cca2__0) {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__norm____pinNumber11 
            = vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber10;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__norm____pinNumber21 
            = vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber20;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__norm____pinNumber22 
            = vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber21;
    } else {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__norm____pinNumber11 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__norm____pinNumber21 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__norm____pinNumber22 = 0U;
    }
    if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75247847__0) {
        bench__DOT__dut__DOT__decoder__DOT____Vcellinp__mlp____pinNumber10 
            = vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber10;
        bench__DOT__dut__DOT__decoder__DOT____Vcellinp__mlp____pinNumber21 
            = vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber21;
        bench__DOT__dut__DOT__decoder__DOT____Vcellinp__mlp____pinNumber20 
            = vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber20;
    } else {
        bench__DOT__dut__DOT__decoder__DOT____Vcellinp__mlp____pinNumber10 = 0U;
        bench__DOT__dut__DOT__decoder__DOT____Vcellinp__mlp____pinNumber21 = 0U;
        bench__DOT__dut__DOT__decoder__DOT____Vcellinp__mlp____pinNumber20 = 0U;
    }
    if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT__mux__DOT__active) {
        bench__DOT__dut__DOT____Vcellout__decoder____pinNumber9 
            = (1U & (bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[4U] 
                     >> 8U));
        bench__DOT__dut__DOT____Vcellout__decoder____pinNumber11 
            = (1U & (bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[4U] 
                     >> 7U));
        bench__DOT__dut__DOT____Vcellout__decoder____pinNumber12 
            = (0xfU & (bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[4U] 
                       >> 3U));
        bench__DOT__dut__DOT____Vcellout__decoder____pinNumber13 
            = ((bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[4U] 
                << 0x1dU) | (bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[3U] 
                             >> 3U));
        bench__DOT__dut__DOT____Vcellout__decoder____pinNumber14 
            = (7U & bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[3U]);
        bench__DOT__dut__DOT____Vcellout__decoder____pinNumber15 
            = bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[2U];
        bench__DOT__dut__DOT____Vcellout__decoder____pinNumber16 
            = bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[1U];
        bench__DOT__dut__DOT____Vcellout__decoder____pinNumber17 
            = bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[0U];
    } else {
        bench__DOT__dut__DOT____Vcellout__decoder____pinNumber9 = 0U;
        bench__DOT__dut__DOT____Vcellout__decoder____pinNumber11 = 0U;
        bench__DOT__dut__DOT____Vcellout__decoder____pinNumber12 = 0U;
        bench__DOT__dut__DOT____Vcellout__decoder____pinNumber13 = 0U;
        bench__DOT__dut__DOT____Vcellout__decoder____pinNumber14 = 0U;
        bench__DOT__dut__DOT____Vcellout__decoder____pinNumber15 = 0U;
        bench__DOT__dut__DOT____Vcellout__decoder____pinNumber16 = 0U;
        bench__DOT__dut__DOT____Vcellout__decoder____pinNumber17 = 0U;
    }
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellinp__gemv____pinNumber11 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h7b2ffeda__0) 
           & (IData)(bench__DOT__dut__DOT__decoder__DOT____Vcellinp__mlp____pinNumber10));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellinp__silu_product____pinNumber11 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h7a913e59__0) 
           & (IData)(bench__DOT__dut__DOT__decoder__DOT____Vcellinp__mlp____pinNumber10));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellinp__silu_product____pinNumber22 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h7a913e59__0) 
           & (IData)(bench__DOT__dut__DOT__decoder__DOT____Vcellinp__mlp____pinNumber21));
    if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h7b2ffeda__0) {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellinp__gemv____pinNumber22 
            = bench__DOT__dut__DOT__decoder__DOT____Vcellinp__mlp____pinNumber21;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellinp__gemv____pinNumber21 
            = bench__DOT__dut__DOT__decoder__DOT____Vcellinp__mlp____pinNumber20;
    } else {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellinp__gemv____pinNumber22 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellinp__gemv____pinNumber21 = 0U;
    }
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellinp__silu_product____pinNumber21 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h7a913e59__0)
            ? bench__DOT__dut__DOT__decoder__DOT____Vcellinp__mlp____pinNumber20
            : 0U);
    __Vtemp_83[0U] = vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_wdata;
    __Vtemp_83[1U] = (IData)((((QData)((IData)(vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_row)) 
                               << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_col))));
    __Vtemp_83[2U] = (IData)(((((QData)((IData)(vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_row)) 
                                << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_col))) 
                              >> 0x20U));
    __Vtemp_83[3U] = ((vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_layer 
                       << 3U) | (IData)(vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_proj));
    __Vtemp_83[4U] = ((bench__DOT__dut__DOT____Vcellout__decoder____pinNumber17 
                       << 9U) | (((IData)(vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_valid) 
                                  << 8U) | (((IData)(vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_write) 
                                             << 7U) 
                                            | (((IData)(vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_kind) 
                                                << 3U) 
                                               | (vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_layer 
                                                  >> 0x1dU)))));
    __Vtemp_83[5U] = ((bench__DOT__dut__DOT____Vcellout__decoder____pinNumber17 
                       >> 0x17U) | ((IData)((((QData)((IData)(bench__DOT__dut__DOT____Vcellout__decoder____pinNumber15)) 
                                              << 0x20U) 
                                             | (QData)((IData)(bench__DOT__dut__DOT____Vcellout__decoder____pinNumber16)))) 
                                    << 9U));
    __Vtemp_83[6U] = (((IData)((((QData)((IData)(bench__DOT__dut__DOT____Vcellout__decoder____pinNumber15)) 
                                 << 0x20U) | (QData)((IData)(bench__DOT__dut__DOT____Vcellout__decoder____pinNumber16)))) 
                       >> 0x17U) | ((IData)(((((QData)((IData)(bench__DOT__dut__DOT____Vcellout__decoder____pinNumber15)) 
                                               << 0x20U) 
                                              | (QData)((IData)(bench__DOT__dut__DOT____Vcellout__decoder____pinNumber16))) 
                                             >> 0x20U)) 
                                    << 9U));
    __Vtemp_83[7U] = ((bench__DOT__dut__DOT____Vcellout__decoder____pinNumber13 
                       << 0xcU) | (((IData)(bench__DOT__dut__DOT____Vcellout__decoder____pinNumber14) 
                                    << 9U) | ((IData)(
                                                      ((((QData)((IData)(bench__DOT__dut__DOT____Vcellout__decoder____pinNumber15)) 
                                                         << 0x20U) 
                                                        | (QData)((IData)(bench__DOT__dut__DOT____Vcellout__decoder____pinNumber16))) 
                                                       >> 0x20U)) 
                                              >> 0x17U)));
    __Vtemp_83[8U] = ((vlSymsp->TOP__bench__DOT__dut__DOT__final_norm.mem_req_wdata 
                       << 0x12U) | (((IData)(bench__DOT__dut__DOT____Vcellout__decoder____pinNumber9) 
                                     << 0x11U) | (((IData)(bench__DOT__dut__DOT____Vcellout__decoder____pinNumber11) 
                                                   << 0x10U) 
                                                  | (((IData)(bench__DOT__dut__DOT____Vcellout__decoder____pinNumber12) 
                                                      << 0xcU) 
                                                     | (bench__DOT__dut__DOT____Vcellout__decoder____pinNumber13 
                                                        >> 0x14U)))));
    __Vtemp_83[9U] = ((vlSymsp->TOP__bench__DOT__dut__DOT__final_norm.mem_req_wdata 
                       >> 0xeU) | ((IData)((((QData)((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__final_norm.mem_req_row)) 
                                             << 0x20U) 
                                            | (QData)((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__final_norm.mem_req_col)))) 
                                   << 0x12U));
    __Vtemp_83[0xaU] = (((IData)((((QData)((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__final_norm.mem_req_row)) 
                                   << 0x20U) | (QData)((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__final_norm.mem_req_col)))) 
                         >> 0xeU) | ((IData)(((((QData)((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__final_norm.mem_req_row)) 
                                                << 0x20U) 
                                               | (QData)((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__final_norm.mem_req_col))) 
                                              >> 0x20U)) 
                                     << 0x12U));
    __Vtemp_83[0xbU] = ((vlSymsp->TOP__bench__DOT__dut__DOT__final_norm.mem_req_layer 
                         << 0x15U) | (((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__final_norm.mem_req_proj) 
                                       << 0x12U) | 
                                      ((IData)(((((QData)((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__final_norm.mem_req_row)) 
                                                  << 0x20U) 
                                                 | (QData)((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__final_norm.mem_req_col))) 
                                                >> 0x20U)) 
                                       >> 0xeU)));
    __Vtemp_83[0xcU] = (((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__final_norm.mem_req_valid) 
                         << 0x1aU) | (((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__final_norm.mem_req_write) 
                                       << 0x19U) | 
                                      (((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__final_norm.mem_req_kind) 
                                        << 0x15U) | 
                                       (vlSymsp->TOP__bench__DOT__dut__DOT__final_norm.mem_req_layer 
                                        >> 0xbU))));
    if ((0x19aU >= (0x1ffU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__selected)))) {
        bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[0U] 
            = (((0U == (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__selected)))
                 ? 0U : (__Vtemp_83[((IData)(1U) + 
                                     (0xfU & (((IData)(0x89U) 
                                               * vlSelf->bench__DOT__dut__DOT__selected) 
                                              >> 5U)))] 
                         << ((IData)(0x20U) - (0x1fU 
                                               & ((IData)(0x89U) 
                                                  * vlSelf->bench__DOT__dut__DOT__selected))))) 
               | (__Vtemp_83[(0xfU & (((IData)(0x89U) 
                                       * vlSelf->bench__DOT__dut__DOT__selected) 
                                      >> 5U))] >> (0x1fU 
                                                   & ((IData)(0x89U) 
                                                      * vlSelf->bench__DOT__dut__DOT__selected))));
        bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[1U] 
            = (((0U == (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__selected)))
                 ? 0U : (__Vtemp_83[((IData)(2U) + 
                                     (0xfU & (((IData)(0x89U) 
                                               * vlSelf->bench__DOT__dut__DOT__selected) 
                                              >> 5U)))] 
                         << ((IData)(0x20U) - (0x1fU 
                                               & ((IData)(0x89U) 
                                                  * vlSelf->bench__DOT__dut__DOT__selected))))) 
               | (__Vtemp_83[((IData)(1U) + (0xfU & 
                                             (((IData)(0x89U) 
                                               * vlSelf->bench__DOT__dut__DOT__selected) 
                                              >> 5U)))] 
                  >> (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__selected))));
        bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[2U] 
            = (((0U == (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__selected)))
                 ? 0U : (__Vtemp_83[((IData)(3U) + 
                                     (0xfU & (((IData)(0x89U) 
                                               * vlSelf->bench__DOT__dut__DOT__selected) 
                                              >> 5U)))] 
                         << ((IData)(0x20U) - (0x1fU 
                                               & ((IData)(0x89U) 
                                                  * vlSelf->bench__DOT__dut__DOT__selected))))) 
               | (__Vtemp_83[((IData)(2U) + (0xfU & 
                                             (((IData)(0x89U) 
                                               * vlSelf->bench__DOT__dut__DOT__selected) 
                                              >> 5U)))] 
                  >> (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__selected))));
        bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[3U] 
            = (((0U == (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__selected)))
                 ? 0U : (__Vtemp_83[((IData)(4U) + 
                                     (0xfU & (((IData)(0x89U) 
                                               * vlSelf->bench__DOT__dut__DOT__selected) 
                                              >> 5U)))] 
                         << ((IData)(0x20U) - (0x1fU 
                                               & ((IData)(0x89U) 
                                                  * vlSelf->bench__DOT__dut__DOT__selected))))) 
               | (__Vtemp_83[((IData)(3U) + (0xfU & 
                                             (((IData)(0x89U) 
                                               * vlSelf->bench__DOT__dut__DOT__selected) 
                                              >> 5U)))] 
                  >> (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__selected))));
        bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[4U] 
            = (0x1ffU & (((0U == (0x1fU & ((IData)(0x89U) 
                                           * vlSelf->bench__DOT__dut__DOT__selected)))
                           ? 0U : (__Vtemp_83[((IData)(5U) 
                                               + (0xfU 
                                                  & (((IData)(0x89U) 
                                                      * vlSelf->bench__DOT__dut__DOT__selected) 
                                                     >> 5U)))] 
                                   << ((IData)(0x20U) 
                                       - (0x1fU & ((IData)(0x89U) 
                                                   * vlSelf->bench__DOT__dut__DOT__selected))))) 
                         | (__Vtemp_83[((IData)(4U) 
                                        + (0xfU & (
                                                   ((IData)(0x89U) 
                                                    * vlSelf->bench__DOT__dut__DOT__selected) 
                                                   >> 5U)))] 
                            >> (0x1fU & ((IData)(0x89U) 
                                         * vlSelf->bench__DOT__dut__DOT__selected)))));
    } else {
        bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[0U] 
            = vlSelf->bench__DOT__dut__DOT__bus__DOT____Vxrand_had98437b__0[0U];
        bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[1U] 
            = vlSelf->bench__DOT__dut__DOT__bus__DOT____Vxrand_had98437b__0[1U];
        bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[2U] 
            = vlSelf->bench__DOT__dut__DOT__bus__DOT____Vxrand_had98437b__0[2U];
        bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[3U] 
            = vlSelf->bench__DOT__dut__DOT__bus__DOT____Vxrand_had98437b__0[3U];
        bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[4U] 
            = (0x1ffU & vlSelf->bench__DOT__dut__DOT__bus__DOT____Vxrand_had98437b__0[4U]);
    }
    if (vlSelf->bench__DOT__dut__DOT__bus__DOT__mux__DOT__active) {
        vlSelf->bench__DOT__mem_req_valid = (1U & (
                                                   bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[4U] 
                                                   >> 8U));
        vlSelf->bench__DOT__mem_req_write = (1U & (
                                                   bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[4U] 
                                                   >> 7U));
        vlSelf->bench__DOT__mem_req_kind = (0xfU & 
                                            (bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[4U] 
                                             >> 3U));
        vlSelf->bench__DOT__mem_req_layer = ((bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[4U] 
                                              << 0x1dU) 
                                             | (bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[3U] 
                                                >> 3U));
        vlSelf->bench__DOT__mem_req_proj = (7U & bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[3U]);
        vlSelf->bench__DOT__mem_req_row = bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[2U];
        vlSelf->bench__DOT__mem_req_col = bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[1U];
        vlSelf->bench__DOT__mem_req_wdata = bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[0U];
    } else {
        vlSelf->bench__DOT__mem_req_valid = 0U;
        vlSelf->bench__DOT__mem_req_write = 0U;
        vlSelf->bench__DOT__mem_req_kind = 0U;
        vlSelf->bench__DOT__mem_req_layer = 0U;
        vlSelf->bench__DOT__mem_req_proj = 0U;
        vlSelf->bench__DOT__mem_req_row = 0U;
        vlSelf->bench__DOT__mem_req_col = 0U;
        vlSelf->bench__DOT__mem_req_wdata = 0U;
    }
}

void Vbench___024root___nba_sequent__TOP__0(Vbench___024root* vlSelf);
void Vbench_anvil_q1_rmsnorm__N1_H8_M4___nba_sequent__TOP__bench__DOT__dut__DOT__decoder__DOT__norm__0(Vbench_anvil_q1_rmsnorm__N1_H8_M4* vlSelf);
void Vbench_anvil_q1_rmsnorm__N1_H8_M4___nba_sequent__TOP__bench__DOT__dut__DOT__final_norm__0(Vbench_anvil_q1_rmsnorm__N1_H8_M4* vlSelf);
void Vbench_anvil_edge_signed_multiplier__pi11___nba_sequent__TOP__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__multiplier__0(Vbench_anvil_edge_signed_multiplier__pi11* vlSelf);
void Vbench_anvil_edge_signed_multiplier__pi11___nba_sequent__TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__multiplier__0(Vbench_anvil_edge_signed_multiplier__pi11* vlSelf);
void Vbench_anvil_edge_signed_multiplier__pi11___nba_sequent__TOP__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__multiplier__0(Vbench_anvil_edge_signed_multiplier__pi11* vlSelf);
void Vbench_anvil_edge_signed_multiplier__pi11___nba_sequent__TOP__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__multiplier__0(Vbench_anvil_edge_signed_multiplier__pi11* vlSelf);
void Vbench_anvil_edge_signed_multiplier__pi11___nba_sequent__TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier__0(Vbench_anvil_edge_signed_multiplier__pi11* vlSelf);
void Vbench_anvil_edge_signed_multiplier__pi11___nba_sequent__TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__multiplier__0(Vbench_anvil_edge_signed_multiplier__pi11* vlSelf);
void Vbench_anvil_edge_signed_multiplier__pi11___nba_sequent__TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__multiplier__0(Vbench_anvil_edge_signed_multiplier__pi11* vlSelf);
void Vbench_anvil_edge_signed_multiplier__pi11___nba_sequent__TOP__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__multiplier__0(Vbench_anvil_edge_signed_multiplier__pi11* vlSelf);
void Vbench___024root___nba_sequent__TOP__1(Vbench___024root* vlSelf);
void Vbench_anvil_edge_signed_multiplier__pi11___nba_sequent__TOP__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__multiplier__1(Vbench_anvil_edge_signed_multiplier__pi11* vlSelf);
void Vbench_anvil_edge_signed_multiplier__pi11___nba_sequent__TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__multiplier__1(Vbench_anvil_edge_signed_multiplier__pi11* vlSelf);
void Vbench_anvil_edge_signed_multiplier__pi11___nba_sequent__TOP__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__multiplier__1(Vbench_anvil_edge_signed_multiplier__pi11* vlSelf);
void Vbench_anvil_edge_signed_multiplier__pi11___nba_sequent__TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__multiplier__1(Vbench_anvil_edge_signed_multiplier__pi11* vlSelf);
void Vbench___024root___nba_sequent__TOP__2(Vbench___024root* vlSelf);
void Vbench___024root___nba_sequent__TOP__3(Vbench___024root* vlSelf);
void Vbench___024root___nba_sequent__TOP__4(Vbench___024root* vlSelf);
void Vbench___024root___nba_sequent__TOP__5(Vbench___024root* vlSelf);
void Vbench___024root___nba_comb__TOP__0(Vbench___024root* vlSelf);
void Vbench_anvil_q1_rmsnorm__N1_H8_M4___nba_comb__TOP__bench__DOT__dut__DOT__decoder__DOT__norm__0(Vbench_anvil_q1_rmsnorm__N1_H8_M4* vlSelf);
void Vbench_anvil_q1_rmsnorm__N1_H8_M4___nba_comb__TOP__bench__DOT__dut__DOT__final_norm__0(Vbench_anvil_q1_rmsnorm__N1_H8_M4* vlSelf);
void Vbench_anvil_edge_signed_multiplier__pi11___nba_comb__TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier__0(Vbench_anvil_edge_signed_multiplier__pi11* vlSelf);
void Vbench_anvil_edge_signed_multiplier__pi11___act_comb__TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier__0(Vbench_anvil_edge_signed_multiplier__pi11* vlSelf);
void Vbench___024root___nba_comb__TOP__1(Vbench___024root* vlSelf);
void Vbench___024root___nba_sequent__TOP__6(Vbench___024root* vlSelf);
void Vbench___024root___nba_sequent__TOP__7(Vbench___024root* vlSelf);
void Vbench___024root___nba_comb__TOP__2(Vbench___024root* vlSelf);
void Vbench_anvil_q1_rmsnorm__N1_H8_M4___nba_comb__TOP__bench__DOT__dut__DOT__final_norm__1(Vbench_anvil_q1_rmsnorm__N1_H8_M4* vlSelf);
void Vbench___024root___nba_sequent__TOP__8(Vbench___024root* vlSelf);
void Vbench___024root___nba_sequent__TOP__9(Vbench___024root* vlSelf);
void Vbench___024root___nba_comb__TOP__4(Vbench___024root* vlSelf);
void Vbench_anvil_q1_rmsnorm__N1_H8_M4___nba_comb__TOP__bench__DOT__dut__DOT__final_norm__2(Vbench_anvil_q1_rmsnorm__N1_H8_M4* vlSelf);
void Vbench_anvil_q1_rmsnorm__N1_H8_M4___nba_comb__TOP__bench__DOT__dut__DOT__decoder__DOT__norm__2(Vbench_anvil_q1_rmsnorm__N1_H8_M4* vlSelf);

void Vbench___024root___eval_nba(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___eval_nba\n"); );
    // Body
    if ((8ULL & vlSelf->__VnbaTriggered.word(0U))) {
        Vbench___024root___nba_sequent__TOP__0(vlSelf);
        Vbench_anvil_q1_rmsnorm__N1_H8_M4___nba_sequent__TOP__bench__DOT__dut__DOT__decoder__DOT__norm__0((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__norm));
        Vbench_anvil_q1_rmsnorm__N1_H8_M4___nba_sequent__TOP__bench__DOT__dut__DOT__final_norm__0((&vlSymsp->TOP__bench__DOT__dut__DOT__final_norm));
        Vbench_anvil_edge_signed_multiplier__pi11___nba_sequent__TOP__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi11___nba_sequent__TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi11___nba_sequent__TOP__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi11___nba_sequent__TOP__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi11___nba_sequent__TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi11___nba_sequent__TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi11___nba_sequent__TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi11___nba_sequent__TOP__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__multiplier));
        Vbench___024root___nba_sequent__TOP__1(vlSelf);
        Vbench_anvil_edge_signed_multiplier__pi11___nba_sequent__TOP__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__multiplier__1((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi11___nba_sequent__TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__multiplier__1((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi11___nba_sequent__TOP__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__multiplier__1((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi11___nba_sequent__TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__multiplier__1((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__multiplier));
        Vbench___024root___nba_sequent__TOP__2(vlSelf);
    }
    if ((4ULL & vlSelf->__VnbaTriggered.word(0U))) {
        Vbench___024root___nba_sequent__TOP__3(vlSelf);
    }
    if ((1ULL & vlSelf->__VnbaTriggered.word(0U))) {
        Vbench___024root___nba_sequent__TOP__4(vlSelf);
    }
    if ((2ULL & vlSelf->__VnbaTriggered.word(0U))) {
        Vbench___024root___nba_sequent__TOP__5(vlSelf);
    }
    if ((0x1eULL & vlSelf->__VnbaTriggered.word(0U))) {
        Vbench___024root___nba_comb__TOP__0(vlSelf);
        Vbench_anvil_q1_rmsnorm__N1_H8_M4___nba_comb__TOP__bench__DOT__dut__DOT__decoder__DOT__norm__0((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__norm));
        Vbench_anvil_q1_rmsnorm__N1_H8_M4___nba_comb__TOP__bench__DOT__dut__DOT__final_norm__0((&vlSymsp->TOP__bench__DOT__dut__DOT__final_norm));
        Vbench_anvil_edge_signed_multiplier__pi11___nba_comb__TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi11___nba_comb__TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi11___nba_comb__TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi11___nba_comb__TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi11___act_comb__TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi11___act_comb__TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi11___act_comb__TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi11___nba_comb__TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__multiplier));
        Vbench___024root___nba_comb__TOP__1(vlSelf);
    }
    if ((8ULL & vlSelf->__VnbaTriggered.word(0U))) {
        Vbench___024root___nba_sequent__TOP__6(vlSelf);
    }
    if ((4ULL & vlSelf->__VnbaTriggered.word(0U))) {
        Vbench___024root___nba_sequent__TOP__7(vlSelf);
    }
    if ((0x1eULL & vlSelf->__VnbaTriggered.word(0U))) {
        Vbench___024root___nba_comb__TOP__2(vlSelf);
        Vbench_anvil_q1_rmsnorm__N1_H8_M4___nba_comb__TOP__bench__DOT__dut__DOT__final_norm__1((&vlSymsp->TOP__bench__DOT__dut__DOT__final_norm));
        Vbench_anvil_q1_rmsnorm__N1_H8_M4___nba_comb__TOP__bench__DOT__dut__DOT__final_norm__1((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__norm));
    }
    if ((8ULL & vlSelf->__VnbaTriggered.word(0U))) {
        Vbench___024root___nba_sequent__TOP__8(vlSelf);
    }
    if ((1ULL & vlSelf->__VnbaTriggered.word(0U))) {
        Vbench___024root___nba_sequent__TOP__9(vlSelf);
    }
    if ((0x1eULL & vlSelf->__VnbaTriggered.word(0U))) {
        Vbench___024root___nba_comb__TOP__3(vlSelf);
    }
    if ((0x1fULL & vlSelf->__VnbaTriggered.word(0U))) {
        Vbench___024root___nba_comb__TOP__4(vlSelf);
        Vbench_anvil_q1_rmsnorm__N1_H8_M4___nba_comb__TOP__bench__DOT__dut__DOT__final_norm__2((&vlSymsp->TOP__bench__DOT__dut__DOT__final_norm));
        Vbench_anvil_q1_rmsnorm__N1_H8_M4___nba_comb__TOP__bench__DOT__dut__DOT__decoder__DOT__norm__2((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__norm));
    }
}
