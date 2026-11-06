# Frozen PIPE direct-display internal CDC candidate, not a board clock/I/O file.
# Caller must bind the exact selected hierarchy; default is the frozen leaf OOC.
# Do not combine with broad clock groups / domain-wide false paths.
if {![info exists DIRECT_DISPLAY_ROOT]} {set DIRECT_DISPLAY_ROOT ""}
set direct_cdc_objects [dict create]
proc direct_exact_reg {relative} {
 global DIRECT_DISPLAY_ROOT
 set name [expr {$DIRECT_DISPLAY_ROOT eq "" ? $relative : "$DIRECT_DISPLAY_ROOT/$relative"}]
 set cells [get_cells -quiet -hier -filter [format {NAME == "%s"} $name]]
 if {[llength $cells]!=1} {error "DIRECT CDC expected one exact register $name; got [llength $cells]"}
 if {![regexp {^FD} [get_property REF_NAME $cells]]} {error "DIRECT CDC non-FF endpoint $name"}
 return $cells
}
proc direct_bit_regs {relative width} {
 set answer {}
 for {set bit 0} {$bit<$width} {incr bit} {lappend answer [direct_exact_reg [format {%s[%d]} $relative $bit]]}
 return $answer
}
proc direct_pins {cells role} {
 set pins [get_pins -quiet -of_objects $cells -filter [format {REF_PIN_NAME == %s} $role]]
 if {[llength $pins]!=[llength $cells]} {error "DIRECT CDC unexpected $role pin count"}
 return $pins
}
proc direct_data_bound {key source destination bound skew} {
 global direct_cdc_objects
 set start [direct_pins $source C];set d [direct_pins $destination D]
 # Register C pins are legal timing startpoints and include C_Q; using Q
 # here would segment paths and invalidate clock/CDC/bus-skew reports.
 # -datapath_only intentionally removes clock-phase setup/hold checks ONLY
 # on these exact endpoints; validity/held-data protocol supplies capture hold.
 set_max_delay -datapath_only $bound -from $start -to $d
 if {$skew>0} {set_bus_skew $skew -from $start -to $d}
 dict set direct_cdc_objects $key [dict create source $source destination $destination max_ns $bound skew_ns $skew]
}
# Use the selected design's generated clocks; this file creates no clocks
# and does not override board port/input/output/reset/SDRAM budgets.
proc direct_period_for {relative} {
 set c [direct_exact_reg $relative];set clocks [get_clocks -quiet -of_objects [direct_pins $c C]]
 if {[llength $clocks]!=1} {error "DIRECT CDC needs one defined clock for $relative"}
 return [get_property PERIOD $clocks]
}
if {![info exists DIRECT_MEM_PERIOD_NS]} {set DIRECT_MEM_PERIOD_NS [direct_period_for front_valid_reg]}
if {![info exists DIRECT_PIXEL_PERIOD_NS]} {set DIRECT_PIXEL_PERIOD_NS [direct_period_for lcd/frame_toggle_reg]}
if {abs($DIRECT_MEM_PERIOD_NS-10.000)>0.001 || abs($DIRECT_PIXEL_PERIOD_NS-34.057649667)>0.010} {error "DIRECT CDC unexpected source clocks: $DIRECT_MEM_PERIOD_NS / $DIRECT_PIXEL_PERIOD_NS ns; rederive protocol budgets"}
# Single-bit toggles/level: only first synchronizer D pins are asynchronous.
foreach bank {0 1} {
 direct_data_bound request_token$bank [direct_exact_reg lcd/request${bank}_reg] [direct_exact_reg [format {lcd/request_sync%s_reg[0]} $bank]] $DIRECT_MEM_PERIOD_NS 0
 direct_data_bound done_token$bank [direct_exact_reg lcd/done${bank}_reg] [direct_exact_reg [format {lcd/done_sync%s_reg[0]} $bank]] $DIRECT_PIXEL_PERIOD_NS 0
 # Request line is held from token launch to return completion. Earliest
 # actual capture uses old second-stage token at the THIRD memory edge.
 direct_data_bound request_line$bank [direct_bit_regs lcd/request_line${bank}_reg 10] [direct_bit_regs lcd/captured_line_reg 10] $DIRECT_MEM_PERIOD_NS 5.000
 # completed_bad is held with done; earliest use is third pixel edge.
 direct_data_bound completed_bad$bank [direct_exact_reg lcd/completed_bad${bank}_reg] [direct_exact_reg lcd/loaded${bank}_reg] $DIRECT_PIXEL_PERIOD_NS 0
}
direct_data_bound frame_token [direct_exact_reg lcd/frame_toggle_reg] [direct_exact_reg {lcd/frame_sync_reg[0]}] $DIRECT_MEM_PERIOD_NS 0
direct_data_bound front_valid [direct_exact_reg front_valid_reg] [direct_exact_reg {lcd/valid_sync_reg[0]}] $DIRECT_PIXEL_PERIOD_NS 0
# Gray counter changes one bit at a source update; bound routes to stage1,
# never cut the stage1->stage2 memory-clock paths.
direct_data_bound underrun_gray [direct_bit_regs lcd/underrun_gray_reg 32] [direct_bit_regs lcd/underrun_sync1_reg 32] $DIRECT_MEM_PERIOD_NS 5.000
# Audit all true synchronizer stages; no attribute is added by this file.
foreach relative {lcd/request_sync0_reg lcd/request_sync1_reg lcd/frame_sync_reg lcd/done_sync0_reg lcd/done_sync1_reg lcd/valid_sync_reg} {
 foreach c [direct_bit_regs $relative 2] {if {[get_property ASYNC_REG $c] ne "1"} {error "DIRECT CDC missing inherited ASYNC_REG: $c"}}
}
foreach relative {lcd/underrun_sync1_reg lcd/underrun_sync2_reg} {
 foreach c [direct_bit_regs $relative 32] {if {[get_property ASYNC_REG $c] ne "1"} {error "DIRECT CDC missing gray ASYNC_REG: $c"}}
}
puts "DIRECT_CDC_TARGETED_OBJECTS [dict size $direct_cdc_objects]"
