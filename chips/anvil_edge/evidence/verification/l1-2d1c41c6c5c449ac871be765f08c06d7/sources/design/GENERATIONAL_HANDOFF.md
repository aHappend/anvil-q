# Generational Silicon Handoff Brief: anvil_q1_reference -> Anvil-Edge

## 1. Parent Silicon Signoff Summary
- **Parent Chip**: `anvil_q1_reference` (`/data/sufeng/anvil-q-line5/workspace/project`)
- **Quartus 17.1 STA Status**: `N/A`
- **Setup WNS (100 MHz / 10.0 ns)**: `N/A ns`
- **Hold WNS**: `N/A ns`
- **Arria 10 GX Physical PCIe HIL**: `N/A` (deterministic=N/A)

## 2. Inherited RTL Modules
- `anvil_q1_00_pkg.sv` (106 lines)
- `anvil_q1_awq_dequant.sv` (38 lines)
- `anvil_q1_bus_mux.sv` (35 lines)
- `anvil_q1_decoder_layer.sv` (107 lines)
- `anvil_q1_elementwise.sv` (91 lines)
- `anvil_q1_gqa_attention.sv` (151 lines)
- `anvil_q1_mem_port.sv` (49 lines)
- `anvil_q1_parameters.sv` (27 lines)
- `anvil_q1_rmsnorm.sv` (113 lines)
- `anvil_q1_rope.sv` (97 lines)
- `anvil_q1_swiglu_mlp.sv` (75 lines)
- `anvil_q1_top.sv` (151 lines)
- `anvil_q1_w4a16_gemv.sv` (183 lines)

## 3. Architectural Evolution Guidelines for Coordinator
- Preserve 100% backward compatibility with parent interfaces and verified numerical modes.
- All large memories (`>= 2 KB`) with byte enables must use explicit byte-lane unpacked arrays (`logic [7:0] mem_b0..bN [0:DEPTH-1]`) so Quartus 17.1 infers hard M20K blocks in <45 seconds.
- Maintain `<= 10.0 ns` (100 MHz+) synchronous register-to-register logic depth.
