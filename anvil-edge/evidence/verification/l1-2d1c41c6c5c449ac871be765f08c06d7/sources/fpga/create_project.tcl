package require ::quartus::project

proc project_input {path} {
    if {[file pathtype $path] ne "relative" ||
        [lsearch -exact [file split $path] ".."] >= 0 ||
        ![file isfile $path]} {
        error "A present project-relative input is required: $path"
    }
    return $path
}

if {$argc != 2} {
    error "Usage: quartus_sh -t fpga/create_project.tcl fpga/BOARD.tcl evidence/FRESH_BUILD"
}
set board_file [project_input [lindex $argv 0]]
set output [lindex $argv 1]
if {[file pathtype $output] ne "relative" ||
    [lsearch -exact [file split $output] ".."] >= 0 ||
    [llength [file split $output]] != 2 ||
    [lindex [file split $output] 0] ne "evidence" ||
    [file exists $output]} {
    error "Build output must be a fresh project-relative directory"
}
if {![file isfile rtl/anvil_edge_top.sv]} {
    error "Run from the delivered project root"
}

# The board description is an integration input, never an inferred pin map.
source $board_file
foreach variable {anvil_board_top anvil_board_sources anvil_board_qips anvil_board_sdc anvil_board_assignments} {
    if {![info exists $variable]} {
        error "Board description must define $variable"
    }
}
if {$anvil_board_top eq "anvil_edge_top" || [llength $anvil_board_sources] == 0 ||
    [llength $anvil_board_qips] == 0 || [llength $anvil_board_sdc] == 0} {
    error "A real board wrapper, installed DDR4 QIP and complete board SDC are required"
}
foreach path [concat $anvil_board_sources $anvil_board_qips $anvil_board_sdc \
    [list $anvil_board_assignments]] {
    project_input $path
}
file mkdir $output
project_new [file join $output anvil_edge] -revision anvil_edge
set_global_assignment -name FAMILY "Arria 10"
set_global_assignment -name DEVICE 10AX115N2F45E1SG
set_global_assignment -name TOP_LEVEL_ENTITY $anvil_board_top
set_global_assignment -name PROJECT_OUTPUT_DIRECTORY output_files
set_global_assignment -name SYSTEMVERILOG_FILE [file join ../.. rtl/anvil_edge_numeric_pkg.sv]
foreach path [lsort [glob rtl/*.sv]] {
    if {$path ne "rtl/anvil_edge_numeric_pkg.sv"} {
        set_global_assignment -name SYSTEMVERILOG_FILE [file join ../.. $path]
    }
}
foreach path [concat [lsort [glob fpga/*.sv]] $anvil_board_sources] {
    set_global_assignment -name SYSTEMVERILOG_FILE [file join ../.. $path]
}
foreach path $anvil_board_qips {
    set_global_assignment -name QIP_FILE [file join ../.. $path]
}
foreach path $anvil_board_sdc {
    set_global_assignment -name SDC_FILE [file join ../.. $path]
}
source $anvil_board_assignments
export_assignments
project_close
