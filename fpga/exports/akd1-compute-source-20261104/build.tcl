# Portable clean source build. Never reads any selected/old checkpoint or BIT.
set akd1Root [file dirname [file normalize [info script]]]
if {[llength $argv]!=2} {error "Usage: build.tcl <fresh-output-directory> <threads>"}
set akd1Out [file normalize [lindex $argv 0]]
set akd1Threads [lindex $argv 1]
cd $akd1Out
set_param general.maxThreads $akd1Threads
if {[version -short] ne "2025.2"} {error "Export binds Vivado2025.2"}
set akd1Info [open [file join $akd1Out tool-parameters.txt] w]
puts $akd1Info "[version]\nflow=clean_full_sources_no_checkpoint_inputs\npart=xc7a100tcsg324-1\ntop=moonshine_top_akd1\nthreads=$akd1Threads\ninput_clock_before_synthesis=20ns\nUSR_ACCESS=4D424B31\nUSERID=B0100004\nbitgen=NOT_RUN"
close $akd1Info
source [file join $akd1Root sources.tcl]
foreach akd1Rom {fixture.hex quantizers.hex} {file copy [file join $akd1Root rtl $akd1Rom] [file join $akd1Out $akd1Rom]}
foreach akd1Xdc {lcd_pins_rev4.xdc sdram_pins_rev4.xdc buttons.xdc platform.xdc} {read_xdc [file join $akd1Root constraints $akd1Xdc]}
synth_design -top moonshine_top_akd1 -part xc7a100tcsg324-1
if {[llength [get_clocks clk_50mhz]]!=1 || [get_property PERIOD [get_clocks clk_50mhz]]!=20.0} {error "Missing pre-synthesis50MHz source clock"}
write_checkpoint [file join $akd1Out synthesized.dcp]
namespace eval ::Akd1ExportConstraints {source [file join $::akd1Root constraints timing-akd1-reviewed.tcl]}
namespace eval ::RomResetProof {variable memo;variable known}
file mkdir [file join $akd1Out pre-opt-proof]
namespace eval ::Akd1ExportPreRom {
 set out [file join $::akd1Out pre-opt-proof]
 source [file join $::akd1Root proofs rom_reset_gate_v003.tcl]
}
set akd1Gate [open [file join $akd1Out netlist-gates.txt] w]
puts $akd1Gate "STRICT_LIVE_ABSENCE_CLOCK_AND_ALL16_ROM_GATES_PASS";close $akd1Gate
write_checkpoint [file join $akd1Out constrained.dcp]
opt_design
place_design
phys_opt_design
route_design
phys_opt_design -directive AggressiveExplore
route_design -directive Explore -tns_cleanup
write_checkpoint [file join $akd1Out akd1-clean-routed.dcp]
file mkdir [file join $akd1Out postroute-proof]
namespace eval ::Akd1ExportPostRom {
 set out [file join $::akd1Out postroute-proof]
 source [file join $::akd1Root proofs rom_reset_gate_v003.tcl]
}
source [file join $akd1Root proofs overlay_reset_gate.tcl]
report_timing_summary -delay_type min_max -report_unconstrained -file [file join $akd1Out timing-summary.rpt]
report_timing -delay_type max -max_paths 30 -file [file join $akd1Out setup-paths.rpt]
report_timing -delay_type min -max_paths 30 -file [file join $akd1Out hold-paths.rpt]
report_clocks -file [file join $akd1Out clocks.rpt]
report_route_status -file [file join $akd1Out route-status.rpt]
report_utilization -hierarchical -file [file join $akd1Out utilization.rpt]
report_io -file [file join $akd1Out io.rpt]
report_drc -file [file join $akd1Out default-drc.rpt]
set akd1DefaultDrcErrors [llength [get_drc_violations -quiet -filter {SEVERITY == Error}]]
report_cdc -details -file [file join $akd1Out cdc.rpt]
report_exceptions -coverage -file [file join $akd1Out exceptions.rpt]
report_bus_skew -file [file join $akd1Out bus-skew.rpt]
report_clock_interaction -file [file join $akd1Out clock-interaction.rpt]
check_timing -verbose -file [file join $akd1Out check-timing.rpt]
foreach {akd1Group akd1Ports} {lcd {lcd_hsync lcd_vsync lcd_data_en lcd_data_r[*] lcd_data_g[*] lcd_data_b[*]} qspi {mcu_spi_d[*] mcu_irq_n} audio {dac_mclk dac_bclk dac_wclk dac_din}} {
 report_timing -to [get_ports $akd1Ports] -delay_type max -max_paths 30 -file [file join $akd1Out $akd1Group-output-setup.rpt]
 report_timing -to [get_ports $akd1Ports] -delay_type min -max_paths 30 -file [file join $akd1Out $akd1Group-output-hold.rpt]
}
namespace eval ::Akd1ExportDrc {
 set akd1Rule [get_drc_checks REQP-1839]
 puts "CLEAN_DRC_RULE CLASS=[get_property CLASS $akd1Rule] NAME=[get_property NAME $akd1Rule]"
 if {[get_property CLASS $akd1Rule] ne "rule_check" || [get_property NAME $akd1Rule] ne "REQP-1839"} {error "Fresh actual DRC rule mismatch"}
 report_property $akd1Rule
 set_property MAX_MESSAGES 100000 $akd1Rule
 report_drc -checks [get_drc_checks REQP-1839] -no_waivers -file [file join $::akd1Out drc-reqp1839-full.rpt]
 set akd1Violations [get_drc_violations -quiet]
 if {[llength $akd1Violations]>=100000} {error "DRC inventory hit reporting capacity"}
 set akd1Inv [open [file join $::akd1Out reqp1839-inventory.txt] w]
 set akd1WarningRamNames {}
 foreach akd1Violation $akd1Violations {
  if {![string match {REQP-1839#*} [get_property NAME $akd1Violation]] || [get_property IS_WAIVED $akd1Violation]} {error "Unexpected/waived DRC inventory entry"}
  set akd1Ram [get_cells -quiet -of_objects $akd1Violation -filter {REF_NAME =~ RAMB*}]
  if {[llength $akd1Ram]!=1} {error "Unresolved RAM violation object"}
  lappend akd1WarningRamNames [get_property NAME $akd1Ram]
  puts $akd1Inv "$akd1Violation cells=[get_cells -quiet -of_objects $akd1Violation]"
  report_property $akd1Violation
 }
 set akd1AllNames [lsort [get_property NAME [get_cells -quiet -hier -filter {REF_NAME == RAMB36E1}]]]
 if {[llength $akd1AllNames]!=106 || [llength [get_cells -quiet -hier -filter {REF_NAME == RAMB18E1}]]!=0 || [lsort -unique $akd1WarningRamNames] ne $akd1AllNames} {error "Exact106 BRAM/warning-cell coverage failed"}
 puts $akd1Inv "ALL106_BRAM_WARNING_CELL_COVERAGE_PASS=1";close $akd1Inv
}
set akd1Summary [open [file join $akd1Out route-gates.txt] w]
set akd1Setup [get_property SLACK [get_timing_paths -delay_type max -max_paths 1]]
set akd1Hold [get_property SLACK [get_timing_paths -delay_type min -max_paths 1]]
puts $akd1Summary "setup=$akd1Setup\nhold=$akd1Hold\ndefault_DRC_errors=$akd1DefaultDrcErrors\nbitgen=NOT_RUN\nselected_image=UNCHANGED\nflow=CLEAN_FULL_SOURCE_NO_INPUT_CHECKPOINT"
close $akd1Summary
puts "CLEAN_FULL_SOURCE_REPORTS_COMPLETE=1"
if {$akd1Setup<=0 || $akd1Hold<=0 || $akd1DefaultDrcErrors!=0} {error "Clean rebuild did not close; reports retained and selected image unchanged"}
