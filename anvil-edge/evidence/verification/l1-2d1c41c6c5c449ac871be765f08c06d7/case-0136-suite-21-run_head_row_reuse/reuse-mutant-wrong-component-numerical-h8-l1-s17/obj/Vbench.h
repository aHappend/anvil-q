// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Primary model header
//
// This header should be included by all source files instantiating the design.
// The class here is then constructed to instantiate the design.
// See the Verilator manual for examples.

#ifndef VERILATED_VBENCH_H_
#define VERILATED_VBENCH_H_  // guard

#include "verilated.h"

class Vbench__Syms;
class Vbench___024root;
class Vbench_anvil_edge_signed_multiplier__pi11;
class Vbench_anvil_q1_rmsnorm__N1_H8_M4;


// This class is the main interface to the Verilated model
class alignas(VL_CACHE_LINE_BYTES) Vbench VL_NOT_FINAL : public VerilatedModel {
  private:
    // Symbol table holding complete model state (owned by this class)
    Vbench__Syms* const vlSymsp;

  public:

    // PORTS
    // The application code writes and reads these signals to
    // propagate new values into/out from the Verilated model.

    // CELLS
    // Public to allow access to /* verilator public */ items.
    // Otherwise the application code can consider these internals.
    Vbench_anvil_q1_rmsnorm__N1_H8_M4* const __PVT__bench__DOT__dut__DOT__final_norm;
    Vbench_anvil_q1_rmsnorm__N1_H8_M4* const __PVT__bench__DOT__dut__DOT__decoder__DOT__norm;
    Vbench_anvil_edge_signed_multiplier__pi11* const __PVT__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier;
    Vbench_anvil_edge_signed_multiplier__pi11* const __PVT__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__multiplier;
    Vbench_anvil_edge_signed_multiplier__pi11* const __PVT__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__multiplier;
    Vbench_anvil_edge_signed_multiplier__pi11* const __PVT__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__multiplier;
    Vbench_anvil_edge_signed_multiplier__pi11* const __PVT__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__multiplier;
    Vbench_anvil_edge_signed_multiplier__pi11* const __PVT__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__multiplier;
    Vbench_anvil_edge_signed_multiplier__pi11* const __PVT__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__multiplier;
    Vbench_anvil_edge_signed_multiplier__pi11* const __PVT__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__multiplier;

    // Root instance pointer to allow access to model internals,
    // including inlined /* verilator public_flat_* */ items.
    Vbench___024root* const rootp;

    // CONSTRUCTORS
    /// Construct the model; called by application code
    /// If contextp is null, then the model will use the default global context
    /// If name is "", then makes a wrapper with a
    /// single model invisible with respect to DPI scope names.
    explicit Vbench(VerilatedContext* contextp, const char* name = "TOP");
    explicit Vbench(const char* name = "TOP");
    /// Destroy the model; called (often implicitly) by application code
    virtual ~Vbench();
  private:
    VL_UNCOPYABLE(Vbench);  ///< Copying not allowed

  public:
    // API METHODS
    /// Evaluate the model.  Application must call when inputs change.
    void eval() { eval_step(); }
    /// Evaluate when calling multiple units/models per time step.
    void eval_step();
    /// Evaluate at end of a timestep for tracing, when using eval_step().
    /// Application must call after all eval() and before time changes.
    void eval_end_step() {}
    /// Simulation complete, run final blocks.  Application must call on completion.
    void final();
    /// Are there scheduled events to handle?
    bool eventsPending();
    /// Returns time at next time slot. Aborts if !eventsPending()
    uint64_t nextTimeSlot();
    /// Trace signals in the model; called by application code
    void trace(VerilatedVcdC* tfp, int levels, int options = 0);
    /// Retrieve name of this model instance (as passed to constructor).
    const char* name() const;

    // Abstract methods from VerilatedModel
    const char* hierName() const override final;
    const char* modelName() const override final;
    unsigned threads() const override final;
    /// Prepare for cloning the model at the process level (e.g. fork in Linux)
    /// Release necessary resources. Called before cloning.
    void prepareClone() const;
    /// Re-init after cloning the model at the process level (e.g. fork in Linux)
    /// Re-allocate necessary resources. Called after cloning.
    void atClone() const;
};

#endif  // guard
