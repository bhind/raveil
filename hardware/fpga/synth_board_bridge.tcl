# Candidate Vivado 2025.1 OOC recipe. No board, pinout, bitstream or programming.
# vivado -mode batch -source <bundle>/synth_board_bridge.tcl \
#   -tclargs <matching-repo> <bundle> <new-output> <exact-part> <python-executable>
if {$argc != 5} { error "expected repo bundle new-output exact-part python-executable" }
lassign $argv repo bundle output part python
set repo [file normalize $repo]
set bundle [file normalize $bundle]
set output [file normalize $output]
if {![regexp {^2025\.1($|[. ])} [version -short]]} { error "requires Vivado 2025.1" }
if {[file exists $output]} { error "output already exists" }
if {[file pathtype $output] ne "absolute" || $output eq $bundle || [string first "$bundle/" "$output/"] == 0} {
    error "output overlaps bundle"
}
cd $repo
# The external verifier binds this script, wrapper, constraints and entire core.
exec $python -m raveil.graph_device_board_bundle verify $bundle 2>@1
set parts [get_parts -quiet $part]
if {[llength $parts] != 1 || [lindex $parts 0] ne $part} { error "exact installed part required" }
set settings_handle [open [file join $bundle settings.txt] r]
set settings [read $settings_handle]
close $settings_handle
if {![regexp {^base=([0-9a-f]{8})\nclock_mhz=([0-9]+)\n$} $settings -> base clock_mhz]} { error "bad settings" }
# Verification above enforces alignment/range. Values are never sourced as Tcl.
file mkdir $output
set sources [lsort [glob [file join $bundle core generated-src *.sv]]]
read_verilog -sv $sources
read_verilog -sv [file join $bundle graph_device_board_bridge.sv]
read_xdc [file join $bundle clock.xdc]
synth_design -top GraphDeviceBoardBridge -part $part -mode out_of_context -generic "BASE_ADDR=32'h$base"
if {[llength [get_cells -hierarchical -filter {IS_BLACKBOX == 1}]] != 0} { error "unresolved black boxes" }
report_utilization -file [file join $output utilization.rpt]
report_timing_summary -file [file join $output timing-estimate.rpt]
write_checkpoint [file join $output board-bridge-ooc.dcp]
set receipt [open [file join $output synthesis-settings.txt] {WRONLY CREAT EXCL}]
puts $receipt "tool=[version -short]\npart=$part\nbase=$base\nclock_mhz=$clock_mhz\nevidence=vendor-synthesis-only\nboard=unassigned\nperformance=not-measured"
close $receipt
