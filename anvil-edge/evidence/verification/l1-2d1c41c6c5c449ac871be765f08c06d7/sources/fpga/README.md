# Production FPGA integration prerequisites

Target: Intel Arria 10 GX `10AX115N2F45E1SG`, Quartus 17.1, one shell clock
at 100 MHz or faster. The shell entry point is `anvil_edge_top`.
This source increment provides the shell, not a runnable board project:
the actual board wrapper, installed DDR4 IP and pin/clock constraints have
not been supplied. Do not synthesize a leaf or a behavioral memory replacement
and call it appliance acceptance.

The board integration must supply the installed DDR4 controller/PHY, actual
calibration output, declared aligned DDR window, real SPI NOR capacity and
address mode, and valid target-board pin assignments. It must synchronize
reset release and DDR calibration, constrain all synchronous and generated
clocks, and close setup and hold without broad false-path waivers. Board
resources and pin assignments are not inferred from the FPGA part number.

The single-outstanding DDR bridge must return a response for every request,
including writes, and preserve write strobes for a partial raw-byte segment
tail. PCIe instrumentation may observe transactions but must not select tokens,
compute tensor addresses, supply reference logits, or substitute for boot.

Compile `rtl/*.sv` as the production hierarchy. Compile the unchanged
`anvil_q1_reference/rtl/*.sv` separately for reference-only use; production
core names now overlap the reference, so mixing the sets creates duplicate
modules. Compile `rtl/anvil_edge_numeric_pkg.sv` before package consumers.
The production `anvil_edge_core_adapter` literally instantiates the derived
`anvil_q1_top`, which uses actual typed DDR tensor operations, not scripted
logits. The independent Verifier must establish numerical equivalence and
physical timing; those are not inferred from the retiming implementation.
No assets are embedded with `initial` or `$readmemh` in production logic.

`anvil_edge_image_loader` supplies real mode-0 NOR reads and acknowledged DDR
payload writes for the version-1 image format in `design/STORAGE.md`. Its
`image_loaded` output is only transfer/CRC staging status, not calibration,
semantic validation or boot commit. Do not connect it directly to inference
admission. `anvil_edge_ddr4_boot_loader` now sequences synchronized calibration,
staging, manifest/directory/token/profile/trie validation and atomic commit.
Its packed committed bundle is described in `design/SPEC.md`; it must feed the
runtime mapper and table clients without intermediate base updates. Idle
reload requires quiescent I/O and memory ownership before asserting `start`.
The top/configuration path connects that ownership boundary. No functional
or physical result is established by these saved RTL sources.

## Installed-controller boundary

`fpga/anvil_edge_ddr4_avalon_bridge.sv` is a synthesizable single-outstanding
adapter, not a DDR controller/PHY. Connect it and the shell to the same
100 MHz+ user clock. `AV_DATA_WIDTH` is a power of two from 32 through 1024
bits (default 512); `AV_ADDRESS_WIDTH` defaults to 26. Avalon addresses count
full data-bus words relative to `DDR_BASE`, while shell addresses count bytes.
The declared DDR base/window must be full-bus-word aligned and fit the real
controller capacity. Low
addressed bytes occupy low data lanes. Burstcount is always one for a
command; explicitly zero-extend it to the installed controller's port width.
Byte enables preserve every shell write strobe, including partial table tails.

The bridge captures a request, registers extended bounds/offset checks,
registers its Avalon address/lane payload, holds a command until waitrequest
deasserts, waits for actual read data, registers lane extraction and holds
the response. A write acknowledgement means the real controller accepted
the ordered Avalon write, not that the DRAM cell was independently read back.
The installed controller must guarantee subsequent same-port read ordering.
`avm_response` is the associated two-bit response code (zero success), sampled
with accepted writes or valid read data; board glue must implement the actual
controller's response/error semantics. `memory_fault` carries real PHY/ECC
fault status. No synthetic data or model decisions may drive this adapter.
Calibration loss or a fault during a command marks its eventual response as
an error without cancelling an outstanding bus command.

`fpga/anvil_edge_reset_sync.sv` asserts reset asynchronously and releases it
after two user-clock edges. Global reset must also reset the installed
controller's user-port epoch; inference recovery does not reset that bridge
or annul a DDR transaction. The shell separately synchronizes calibration.

## Board project construction

Required tools are Quartus Prime 17.1 with Arria 10 device support and the
board's installed/generated DDR4 QIP. A board description under `fpga/`
must define these Tcl variables:

| Variable | Required value |
| --- | --- |
| `anvil_board_top` | Real physical wrapper instantiating `anvil_edge_top`, the bridge and installed DDR4 IP. |
| `anvil_board_sources` | Project-relative wrapper/glue SystemVerilog inputs. |
| `anvil_board_qips` | Nonempty list of project-relative installed/generated DDR4 QIP inputs. |
| `anvil_board_sdc` | Nonempty list of complete project-relative board/DDR clock and I/O constraints. |
| `anvil_board_assignments` | Project-relative Tcl with actual pin, I/O-standard and board assignments. |

Paths must exist and may not be absolute or contain `..`. The builder refuses
an existing output directory or a bare shell as physical top. From the
delivered root, once those real inputs exist, the construction command is:

```
quartus_sh -t fpga/create_project.tcl fpga/BOARD.tcl evidence/FRESH_BUILD
quartus_sh --flow compile evidence/FRESH_BUILD/anvil_edge
quartus_sta evidence/FRESH_BUILD/anvil_edge
```

`BOARD.tcl` and `FRESH_BUILD` denote the supplied board description and a new
unused evidence name, respectively; no such board file or completed build is
claimed here. Native shared-runtime gates remain the authoritative timing/HIL
commands, not this project-construction recipe.

Constrain the shell user clock to at most 10.0 ns and all genuine generated/
DDR clocks. Constrain synchronous stream/config/bridge I/O for the actual
wrapper. Limit UART/calibration CDC exceptions to their first synchronizer
stages, constrain SPI against actual NOR setup/hold, and use legitimate reset
recovery/removal treatment. Do not blanket-false-path synchronous endpoints.
The part number does not supply board pins or safe external timing values.

Reset initiates external-image boot automatically after calibration. No
configuration writes are required. After `boot_done`, send raw bytes ending
in LF (LF removed), configured fixed byte count, or bypass `tlast`. Await
response completion before the next prompt. Optional idle configuration uses
the offsets in `design/SPEC.md`; recovery is command bit 0 at 0x1c.
Default flash addressing is 24-bit READ 0x03 and 16 MiB capacity. Actual model
images larger than that require explicit 32-bit READ 0x13 mode and a declared,
physically present capacity; neither flash nor DDR addresses may wrap.
The default core geometry is not a claim that it fits the default external
storage window. Size the real image and declare adequate installed storage.

Native shared-runtime timing and hardware gates remain mandatory. The
independent Verifier owns portable L1 and clean reproduction. No gate has been
executed or passed by this design increment.
