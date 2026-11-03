# Verilated -*- Makefile -*-
# DESCRIPTION: Verilator output: Make include file with class lists
#
# This file lists generated Verilated files, for including in higher level makefiles.
# See Vbench.mk for the caller.

### Switches...
# C11 constructs required?  0/1 (always on now)
VM_C11 = 1
# Timing enabled?  0/1
VM_TIMING = 1
# Coverage output mode?  0/1 (from --coverage)
VM_COVERAGE = 0
# Parallel builds?  0/1 (from --output-split)
VM_PARALLEL_BUILDS = 1
# Tracing output mode?  0/1 (from --trace/--trace-fst)
VM_TRACE = 0
# Tracing output mode in VCD format?  0/1 (from --trace)
VM_TRACE_VCD = 0
# Tracing output mode in FST format?  0/1 (from --trace-fst)
VM_TRACE_FST = 0

### Object file lists...
# Generated module classes, fast-path, compile with highest optimization
VM_CLASSES_FAST += \
	Vbench \
	Vbench___024root__DepSet_h0cc030f4__0 \
	Vbench___024root__DepSet_h0cc030f4__1 \
	Vbench___024root__DepSet_h0cc030f4__2 \
	Vbench___024root__DepSet_h97d444dc__0 \
	Vbench_anvil_q1_rmsnorm__N1_H8_M4__DepSet_h66b0b4e8__0 \
	Vbench_anvil_q1_rmsnorm__N1_H8_M4__DepSet_h66b0b4e8__1 \
	Vbench_anvil_q1_rmsnorm__N1_H8_M4__DepSet_h66b0b4e8__2 \
	Vbench_anvil_q1_rmsnorm__N1_H8_M4__DepSet_h6da4c0c0__0 \
	Vbench_anvil_edge_signed_multiplier__pi11__DepSet_hf17ee4c1__0 \
	Vbench_anvil_edge_signed_multiplier__pi11__DepSet_hf17ee4c1__1 \
	Vbench_anvil_edge_signed_multiplier__pi11__DepSet_hfd6690a9__0 \
	Vbench__main \

# Generated module classes, non-fast-path, compile with low/medium optimization
VM_CLASSES_SLOW += \
	Vbench__ConstPool_0 \
	Vbench___024root__Slow \
	Vbench___024root__DepSet_h0cc030f4__0__Slow \
	Vbench___024root__DepSet_h97d444dc__0__Slow \
	Vbench_anvil_q1_rmsnorm__N1_H8_M4__Slow \
	Vbench_anvil_q1_rmsnorm__N1_H8_M4__DepSet_h66b0b4e8__0__Slow \
	Vbench_anvil_q1_rmsnorm__N1_H8_M4__DepSet_h6da4c0c0__0__Slow \
	Vbench_anvil_edge_signed_multiplier__pi11__Slow \
	Vbench_anvil_edge_signed_multiplier__pi11__DepSet_hf17ee4c1__0__Slow \
	Vbench_anvil_edge_signed_multiplier__pi11__DepSet_hfd6690a9__0__Slow \

# Generated support classes, fast-path, compile with highest optimization
VM_SUPPORT_FAST += \

# Generated support classes, non-fast-path, compile with low/medium optimization
VM_SUPPORT_SLOW += \
	Vbench__Syms \

# Global classes, need linked once per executable, fast-path, compile with highest optimization
VM_GLOBAL_FAST += \
	verilated \
	verilated_timing \
	verilated_threads \

# Global classes, need linked once per executable, non-fast-path, compile with low/medium optimization
VM_GLOBAL_SLOW += \


# Verilated -*- Makefile -*-
